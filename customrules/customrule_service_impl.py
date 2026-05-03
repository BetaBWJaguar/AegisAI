from datetime import datetime
from typing import List, Optional
import uuid

from pymongo import MongoClient

from config_loader import ConfigLoader
from customrules.create.create import RuleCreate
from customrules.customrule import CustomRule
from customrules.customrule_action import CustomRuleAction
from customrules.customrule_service import CustomRuleService
from customrules.customrule_type import CustomRuleType
from customrules.upsert.upsert import RuleUpsert


class CustomRuleServiceImpl(CustomRuleService):
    def __init__(self, config_file: str):
        cfg = ConfigLoader(config_file).get_database_config()

        uri = f"mongodb://{cfg['username']}:{cfg['password']}@" \
              f"{cfg['host']}:{cfg['port']}/{cfg['authSource']}"
        self.client = MongoClient(uri)
        self.db = self.client[cfg["name"]]
        self.collection = self.db["custom_rules"]
        self.collection.create_index("id", unique=True)
        self.collection.create_index("workspace_id")
        self.collection.create_index("rule_type")

    def create_rule(self, data: RuleCreate, created_by: Optional[str] = None) -> CustomRule:
        rule = CustomRule.create(
            name=data.name,
            rule_type=data.rule_type,
            pattern=data.pattern,
            action=data.action,
            description=data.description,
            scope=data.scope,
            priority=data.priority,
            enabled=data.enabled,
            case_sensitive=data.case_sensitive,
            tags=data.tags,
            metadata=data.metadata,
            workspace_id=data.workspace_id,
            created_by=created_by,
        )

        self.collection.insert_one(rule.to_dict())
        return rule

    def get_rule(self, rule_id: str) -> Optional[CustomRule]:
        doc = self.collection.find_one({"id": rule_id})
        return self._from_document(doc) if doc else None

    def list_rules(
        self,
        workspace_id: Optional[str] = None,
        rule_type: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[CustomRule]:
        query: dict = {}

        if workspace_id is not None:
            query["workspace_id"] = workspace_id

        if rule_type is not None:
            query["rule_type"] = rule_type

        if enabled_only:
            query["enabled"] = True

        cursor = self.collection.find(query)
        return [self._from_document(doc) for doc in cursor]

    def update_rule(self, rule_id: str, data: RuleUpsert) -> Optional[CustomRule]:
        existing = self.collection.find_one({"id": rule_id})
        if not existing:
            return None

        update_fields = {}
        for field_name, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                update_fields[field_name] = value

        if not update_fields:
            return self._from_document(existing)

        update_fields["updated_at"] = datetime.utcnow().isoformat()

        self.collection.update_one(
            {"id": rule_id},
            {"$set": update_fields},
        )

        updated_doc = self.collection.find_one({"id": rule_id})
        return self._from_document(updated_doc) if updated_doc else None

    def delete_rule(self, rule_id: str) -> bool:
        result = self.collection.delete_one({"id": rule_id})
        return result.deleted_count > 0

    def _from_document(self, doc: dict) -> CustomRule:
        return CustomRule(
            id=uuid.UUID(doc["id"]),
            name=doc["name"],
            rule_type=CustomRuleType(doc["rule_type"]),
            pattern=doc["pattern"],
            action=CustomRuleAction(doc["action"]),
            description=doc.get("description"),
            scope=doc.get("scope"),
            priority=doc.get("priority", 0),
            enabled=doc.get("enabled", True),
            case_sensitive=doc.get("case_sensitive", False),
            tags=doc.get("tags", []),
            metadata=doc.get("metadata", {}),
            workspace_id=doc.get("workspace_id"),
            created_by=doc.get("created_by"),
            created_at=datetime.fromisoformat(doc["created_at"]) if isinstance(doc.get("created_at"), str) else doc.get("created_at", datetime.utcnow()),
            updated_at=datetime.fromisoformat(doc["updated_at"]) if isinstance(doc.get("updated_at"), str) else doc.get("updated_at", datetime.utcnow()),
            _id=str(doc.get("_id", "")),
        )
