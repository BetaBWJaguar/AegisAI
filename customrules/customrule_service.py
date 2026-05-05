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
    def get_rule(self, rule_id: str) -> Optional[CustomRule]:
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
    def update_rule(self, rule_id: str, data: RuleUpsert) -> Optional[CustomRule]:
        pass

    @abstractmethod
    def delete_rule(self, rule_id: str) -> bool:
        pass

    @abstractmethod
    def toggle_rule(self, rule_id: str) -> Optional[CustomRule]:
        pass

    @abstractmethod
    def search_rules(
        self,
        query: str,
        workspace_id: Optional[str] = None,
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
