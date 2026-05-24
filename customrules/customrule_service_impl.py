import logging
import re
from datetime import datetime
from typing import List, Optional
import uuid

from pymongo import MongoClient

from config_loader import ConfigLoader
from customrules.create.create import RuleCreate
from customrules.customrule import CustomRule
from customrules.customrule_service import CustomRuleService
from customrules.customrule_type import CustomRuleType
from customrules.customruleengine import CustomRuleEngine, EngineConfig
from customrules.upsert.upsert import RuleUpsert

logger = logging.getLogger(__name__)


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
        self.collection.create_index(
            [("name", "text"), ("pattern", "text"), ("description", "text")],
            name="rule_text_search",
        )

        self._engine = CustomRuleEngine(config=EngineConfig())

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

        rule.validate()
        self.collection.insert_one(rule.to_dict())
        return rule

    def get_rule(self, rule_id: str, workspace_id: str) -> Optional[CustomRule]:
        doc = self.collection.find_one({"id": rule_id, "workspace_id": workspace_id})
        return self._from_document(doc) if doc else None

    def list_rules(
            self,
            workspace_id: Optional[str] = None,
            rule_type: Optional[str] = None,
            enabled_only: bool = False,
    ) -> List[CustomRule]:
        query = {k: v for k, v in {"workspace_id": workspace_id, "rule_type": rule_type}.items() if v is not None}
        if enabled_only:
            query["enabled"] = True

        return [self._from_document(doc) for doc in self.collection.find(query).sort("priority", -1)]

    def update_rule(self, rule_id: str, workspace_id: str, data: RuleUpsert) -> Optional[CustomRule]:
        filter_q = {"id": rule_id, "workspace_id": workspace_id}

        update_fields = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not update_fields:
            return self._from_document(self.collection.find_one(filter_q))

        update_fields["updated_at"] = datetime.utcnow().isoformat()
        self.collection.update_one(filter_q, {"$set": update_fields})

        return self._from_document(self.collection.find_one(filter_q))

    def delete_rule(self, rule_id: str, workspace_id: str) -> bool:
        result = self.collection.delete_one({"id": rule_id, "workspace_id": workspace_id})
        return result.deleted_count > 0

    def toggle_rule(self, rule_id: str, workspace_id: str) -> Optional[CustomRule]:
        doc = self.collection.find_one({"id": rule_id, "workspace_id": workspace_id})
        if not doc:
            return None

        new_enabled = not doc.get("enabled", True)
        self.collection.update_one(
            {"id": rule_id, "workspace_id": workspace_id},
            {"$set": {"enabled": new_enabled, "updated_at": datetime.utcnow().isoformat()}},
        )

        updated_doc = self.collection.find_one({"id": rule_id, "workspace_id": workspace_id})
        return self._from_document(updated_doc) if updated_doc else None

    def search_rules(
        self,
        query: str,
        workspace_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[CustomRule]:
        safe_query = re.escape(query)
        mongo_query: dict = {
            "$or": [
                {"name": {"$regex": safe_query, "$options": "i"}},
                {"pattern": {"$regex": safe_query, "$options": "i"}},
                {"description": {"$regex": safe_query, "$options": "i"}},
            ]
        }

        if workspace_id is not None:
            mongo_query["workspace_id"] = workspace_id

        cursor = (
            self.collection
            .find(mongo_query)
            .sort("priority", -1)
            .skip(max(skip, 0))
            .limit(max(limit, 1))
        )
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

    def duplicate_rule(self, rule_id: str, workspace_id: str, created_by: Optional[str] = None) -> Optional[CustomRule]:
        doc = self.collection.find_one({"id": rule_id, "workspace_id": workspace_id})
        if not doc:
            return None

        now = datetime.utcnow().isoformat()
        doc.pop("_id", None)

        new_doc = {
            **doc,
            "id": str(uuid.uuid4()),
            "name": f"{doc['name']} (Copy)",
            "hit_count": 0,
            "last_triggered_at": None,
            "created_by": created_by,
            "created_at": now,
            "updated_at": now
        }

        self.collection.insert_one(new_doc)
        return self._from_document(new_doc)

    def test_pattern(self, pattern: str, rule_type: str, test_text: str, case_sensitive: bool = False) -> dict:
        try:
            rt = CustomRuleType(rule_type)
        except ValueError:
            return {"error": f"Invalid rule_type: {rule_type}", "matches": []}

        return self._engine.test_pattern(
            pattern=pattern,
            rule_type=rt,
            test_text=test_text,
            case_sensitive=case_sensitive,
        )

    def evaluate_text(self, text: str, workspace_id: str) -> dict:
        rules = self.list_rules(workspace_id=workspace_id, enabled_only=True)

        if not rules:
            return {
                "text": text,
                "matched": False,
                "triggered_rules": [],
                "processed_text": text,
            }

        def _on_rule_triggered(rule: CustomRule, result) -> None:
            rule.record_hit()
            self.collection.update_one(
                {"id": str(rule.id), "workspace_id": workspace_id},
                {
                    "$set": {
                        "hit_count": rule.hit_count,
                        "last_triggered_at": datetime.utcnow().isoformat(),
                    }
                },
            )

        engine = CustomRuleEngine(
            config=EngineConfig(),
            on_rule_triggered=_on_rule_triggered,
        )

        engine_result = engine.evaluate(text, rules)

        triggered_rules = [
            {
                "rule_id": tr.rule_id,
                "rule_name": tr.rule_name,
                "rule_type": tr.rule_type,
                "action": tr.action,
                "priority": tr.priority,
                "match_count": tr.match_count,
                "matches": tr.matches,
                **({"replace_text": tr.replace_text} if tr.replace_text is not None else {}),
                **({"highlighted_text": tr.highlighted_text} if tr.highlighted_text is not None else {}),
            }
            for tr in engine_result.triggered_rules
        ]

        return {
            "text": engine_result.original_text,
            "matched": engine_result.matched,
            "triggered_rule_count": engine_result.triggered_rule_count,
            "triggered_rules": triggered_rules,
            "processed_text": engine_result.processed_text,
            "highlighted_original": engine_result.highlighted_original,
            "verdict": engine_result.verdict.value,
        }

    def bulk_toggle(self, rule_ids: List[str], enabled: bool, workspace_id: Optional[str] = None) -> List[CustomRule]:
        now = datetime.utcnow().isoformat()

        query: dict = {"id": {"$in": rule_ids}}
        if workspace_id is not None:
            query["workspace_id"] = workspace_id

        self.collection.update_many(
            query,
            {"$set": {"enabled": enabled, "updated_at": now}},
        )

        cursor = self.collection.find(query)
        return [self._from_document(doc) for doc in cursor]

    def get_rules_by_tag(self, tag: str, workspace_id: Optional[str] = None) -> List[CustomRule]:
        query: dict = {"tags": tag}

        if workspace_id is not None:
            query["workspace_id"] = workspace_id

        cursor = self.collection.find(query)
        return [self._from_document(doc) for doc in cursor]

    def bulk_delete(self, rule_ids: List[str], workspace_id: Optional[str] = None) -> int:
        query: dict = {"id": {"$in": rule_ids}}

        if workspace_id is not None:
            query["workspace_id"] = workspace_id

        result = self.collection.delete_many(query)
        return result.deleted_count

    def _from_document(self, doc: dict) -> CustomRule:
        return CustomRule.from_dict(doc)

    def get_active_rules_by_priority(
            self,
            workspace_id: str,
            rule_type: Optional[str] = None,
    ) -> List[CustomRule]:
        query: dict = {
            "workspace_id": workspace_id,
            "enabled": True,
        }

        if rule_type is not None:
            query["rule_type"] = rule_type

        cursor = self.collection.find(query).sort("priority", -1)
        return [self._from_document(doc) for doc in cursor]

    def export_rules_to_json(
            self,
            workspace_id: Optional[str] = None,
            rule_type: Optional[str] = None,
            enabled_only: bool = False,
            include_metadata: bool = True,
            include_hit_stats: bool = False,
    ) -> dict:
        rules = self.list_rules(
            workspace_id=workspace_id,
            rule_type=rule_type,
            enabled_only=enabled_only,
        )

        exported_rules: List[dict] = []
        for rule in rules:
            rule_dict = rule.to_dict()

            if not include_metadata:
                rule_dict.pop("metadata", None)

            if not include_hit_stats:
                rule_dict.pop("hit_count", None)
                rule_dict.pop("last_triggered_at", None)

            rule_dict.pop("_id", None)

            exported_rules.append(rule_dict)

        filter_info: dict = {}
        if workspace_id is not None:
            filter_info["workspace_id"] = workspace_id
        if rule_type is not None:
            filter_info["rule_type"] = rule_type
        if enabled_only:
            filter_info["enabled_only"] = True

        return {
            "exported_at": datetime.utcnow().isoformat(),
            "filter": filter_info,
            "include_metadata": include_metadata,
            "include_hit_stats": include_hit_stats,
            "total_rules": len(exported_rules),
            "rules": exported_rules,
        }
