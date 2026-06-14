from abc import ABC, abstractmethod
from typing import List, Optional

from customrules.create.create import RuleCreate
from customrules.customrule import CustomRule
from customrules.upsert.upsert import RuleUpsert


class CustomRuleService(ABC):

    @abstractmethod
    def create_rule(self, data: RuleCreate, created_by: Optional[str] = None) -> CustomRule:
        pass

    @abstractmethod
    def get_rule(self, rule_id: str, workspace_id: str) -> Optional[CustomRule]:
        pass

    @abstractmethod
    def list_rules(
        self,
        workspace_id: Optional[str] = None,
        rule_type: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[CustomRule]:
        pass

    @abstractmethod
    def update_rule(self, rule_id: str, workspace_id: str, data: RuleUpsert) -> Optional[CustomRule]:
        pass

    @abstractmethod
    def delete_rule(self, rule_id: str, workspace_id: str) -> bool:
        pass

    @abstractmethod
    def toggle_rule(self, rule_id: str, workspace_id: str) -> Optional[CustomRule]:
        pass

    @abstractmethod
    def search_rules(
        self,
        query: str,
        workspace_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[CustomRule]:
        pass

    @abstractmethod
    def count_rules(
        self,
        workspace_id: Optional[str] = None,
        rule_type: Optional[str] = None,
        enabled_only: bool = False,
    ) -> int:
        pass

    @abstractmethod
    def delete_rules_by_workspace(self, workspace_id: str) -> int:
        pass

    @abstractmethod
    def duplicate_rule(self, rule_id: str, workspace_id: str, created_by: Optional[str] = None) -> Optional[CustomRule]:
        pass

    @abstractmethod
    def test_pattern(self, pattern: str, rule_type: str, test_text: str, case_sensitive: bool = False) -> dict:
        pass

    @abstractmethod
    def bulk_toggle(self, rule_ids: List[str], enabled: bool, workspace_id: Optional[str] = None) -> List[CustomRule]:
        pass

    @abstractmethod
    def get_rules_by_tag(self, tag: str, workspace_id: Optional[str] = None) -> List[CustomRule]:
        pass

    @abstractmethod
    def bulk_delete(self, rule_ids: List[str], workspace_id: Optional[str] = None) -> int:
        pass

    @abstractmethod
    def evaluate_text(
        self,
        text: str,
        workspace_id: str,
        scope: Optional[str] = None,
    ) -> dict:
        pass

    @abstractmethod
    def get_rule_statistics(
        self,
        workspace_id: Optional[str] = None,
    ) -> dict:
        pass

    @abstractmethod
    def get_active_rules_by_priority(
            self,
            workspace_id: str,
            rule_type: Optional[str] = None,
    ) -> List[CustomRule]:
        pass

    @abstractmethod
    def export_rules_to_json(
            self,
            workspace_id: Optional[str] = None,
            rule_type: Optional[str] = None,
            enabled_only: bool = False,
            include_metadata: bool = True,
            include_hit_stats: bool = False,
    ) -> dict:
        pass

    @abstractmethod
    def import_rules_from_json(
            self,
            data: dict,
            workspace_id: Optional[str] = None,
            overwrite: bool = False,
            created_by: Optional[str] = None,
    ) -> dict:
        pass
