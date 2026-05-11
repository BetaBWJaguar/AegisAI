import difflib
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

        elif rt == CustomRuleType.PATTERN:
            try:
                compiled = re.compile(pattern, flags)
                for m in compiled.finditer(test_text):
                    matches.append({
                        "match": m.group(),
                        "start": m.start(),
                        "end": m.end(),
                    })
            except re.error as e:
                return {"error": f"Invalid pattern: {e}", "matches": []}

        elif rt == CustomRuleType.EXACT:
            cmp_text = test_text if case_sensitive else test_text.lower()
            cmp_pattern = pattern if case_sensitive else pattern.lower()
            if cmp_text == cmp_pattern:
                matches.append({
                    "match": test_text,
                    "start": 0,
                    "end": len(test_text),
                })

        elif rt == CustomRuleType.DYNAMIC:
            try:
                wrapped = r"\b(?:%s)\b" % pattern
                compiled = re.compile(wrapped, flags)
                for m in compiled.finditer(test_text):
                    matches.append({
                        "match": m.group(),
                        "start": m.start(),
                        "end": m.end(),
                    })
            except re.error as e:
                return {"error": f"Invalid dynamic pattern: {e}", "matches": []}

        elif rt == CustomRuleType.SEMANTIC:
            pattern_words = pattern.split()
            test_words = test_text.split()
            if not case_sensitive:
                pattern_words = [w.lower() for w in pattern_words]
                test_words = [w.lower() for w in test_words]

            pattern_lower = [w.lower() for w in pattern.split()]
            for i in range(len(test_words)):
                for j in range(i + 1, min(i + len(pattern_words) + 1, len(test_words) + 1)):
                    segment = test_words[i:j]
                    similarity = difflib.SequenceMatcher(
                        None, pattern_lower, [w.lower() for w in segment]
                    ).ratio()
                    if similarity >= 0.7:
                        original_segment = test_text.split()[i:j]
                        matched_text = " ".join(original_segment)
                        start = len(" ".join(test_text.split()[:i])) + (1 if i > 0 else 0)
                        end = start + len(matched_text)
                        matches.append({
                            "match": matched_text,
                            "start": start,
                            "end": end,
                            "similarity": round(similarity, 3),
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
