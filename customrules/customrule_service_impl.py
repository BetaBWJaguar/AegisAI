import fnmatch
import re
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
        self.collection.create_index("tags")

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
            replace_text=data.replace_text,
        )

        rule.validate_pattern()
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

        cursor = self.collection.find(query).sort("priority", -1)
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

    def toggle_rule(self, rule_id: str) -> Optional[CustomRule]:
        doc = self.collection.find_one({"id": rule_id})
        if not doc:
            return None

        new_enabled = not doc.get("enabled", True)
        self.collection.update_one(
            {"id": rule_id},
            {"$set": {"enabled": new_enabled, "updated_at": datetime.utcnow().isoformat()}},
        )

        updated_doc = self.collection.find_one({"id": rule_id})
        return self._from_document(updated_doc) if updated_doc else None

    def search_rules(
        self,
        query: str,
        workspace_id: Optional[str] = None,
    ) -> List[CustomRule]:
        mongo_query: dict = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"pattern": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
            ]
        }

        if workspace_id is not None:
            mongo_query["workspace_id"] = workspace_id

        cursor = self.collection.find(mongo_query)
        return [self._from_document(doc) for doc in cursor]

    def count_rules(
        self,
        workspace_id: Optional[str] = None,
        rule_type: Optional[str] = None,
        enabled_only: bool = False,
    ) -> int:
        query: dict = {}

        if workspace_id is not None:
            query["workspace_id"] = workspace_id

        if rule_type is not None:
            query["rule_type"] = rule_type

        if enabled_only:
            query["enabled"] = True

        return self.collection.count_documents(query)

    def delete_rules_by_workspace(self, workspace_id: str) -> int:
        result = self.collection.delete_many({"workspace_id": workspace_id})
        return result.deleted_count

    def duplicate_rule(self, rule_id: str, created_by: Optional[str] = None) -> Optional[CustomRule]:
        doc = self.collection.find_one({"id": rule_id})
        if not doc:
            return None

        now = datetime.utcnow()
        new_id = str(uuid.uuid4())

        new_doc = dict(doc)
        new_doc.pop("_id", None)
        new_doc["id"] = new_id
        new_doc["name"] = f"{doc['name']} (Copy)"
        new_doc["hit_count"] = 0
        new_doc["last_triggered_at"] = None
        new_doc["created_by"] = created_by
        new_doc["created_at"] = now.isoformat()
        new_doc["updated_at"] = now.isoformat()

        self.collection.insert_one(new_doc)

        return self._from_document(new_doc)

    def test_pattern(self, pattern: str, rule_type: str, test_text: str, case_sensitive: bool = False) -> dict:
        matches: List[dict] = []

        try:
            rt = CustomRuleType(rule_type)
        except ValueError:
            return {"error": f"Invalid rule_type: {rule_type}", "matches": []}

        flags = 0 if case_sensitive else re.IGNORECASE

        if rt == CustomRuleType.REGEX:
            try:
                compiled = re.compile(pattern, flags)
                for m in compiled.finditer(test_text):
                    matches.append({
                        "match": m.group(),
                        "start": m.start(),
                        "end": m.end(),
                    })
            except re.error as e:
                return {"error": f"Invalid regex: {e}", "matches": []}

        elif rt == CustomRuleType.KEYWORD:
            search_text = test_text if case_sensitive else test_text.lower()
            search_pattern = pattern if case_sensitive else pattern.lower()
            start = 0
            while True:
                idx = search_text.find(search_pattern, start)
                if idx == -1:
                    break
                matches.append({
                    "match": test_text[idx:idx + len(pattern)],
                    "start": idx,
                    "end": idx + len(pattern),
                })
                start = idx + 1

        elif rt == CustomRuleType.WILDCARD:
            matched = fnmatch.fnmatch(test_text, pattern)
            if matched:
                matches.append({
                    "match": test_text,
                    "start": 0,
                    "end": len(test_text),
                })

        else:
            return {"error": f"Test not supported for rule_type: {rule_type}", "matches": []}

        return {
            "pattern": pattern,
            "rule_type": rule_type,
            "test_text": test_text,
            "case_sensitive": case_sensitive,
            "match_count": len(matches),
            "matches": matches,
        }

    def bulk_toggle(self, rule_ids: List[str], enabled: bool) -> List[CustomRule]:
        now = datetime.utcnow().isoformat()
        self.collection.update_many(
            {"id": {"$in": rule_ids}},
            {"$set": {"enabled": enabled, "updated_at": now}},
        )

        cursor = self.collection.find({"id": {"$in": rule_ids}})
        return [self._from_document(doc) for doc in cursor]

    def get_rules_by_tag(self, tag: str, workspace_id: Optional[str] = None) -> List[CustomRule]:
        query: dict = {"tags": tag}

        if workspace_id is not None:
            query["workspace_id"] = workspace_id

        cursor = self.collection.find(query)
        return [self._from_document(doc) for doc in cursor]

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
            hit_count=doc.get("hit_count", 0),
            last_triggered_at=(
                datetime.fromisoformat(doc["last_triggered_at"])
                if doc.get("last_triggered_at") and isinstance(doc["last_triggered_at"], str)
                else doc.get("last_triggered_at")
            ),
            replace_text=doc.get("replace_text"),
        )
