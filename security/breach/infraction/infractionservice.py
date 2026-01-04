from abc import ABC, abstractmethod
from typing import Optional
from security.breach.infraction.infraction_result import InfractionResult
from security.breach.actions.actiondecision import ActionDecision
from security.breach.doxxing_settings import DoxxingSettings


class InfractionService(ABC):

    @abstractmethod
    def analyze(self, text: str, doxxing_settings: Optional[DoxxingSettings] = None, lang_code: str = "tr") -> InfractionResult:
        pass

    @abstractmethod
    def analyze_risk(self, text: str, doxxing_settings: Optional[DoxxingSettings] = None, lang_code: str = "tr") -> tuple[str, float, bool]:
        pass

    @abstractmethod
    def decide_action(self, text: str, doxxing_settings: Optional[DoxxingSettings] = None, lang_code: str = "tr") -> ActionDecision:
        pass
