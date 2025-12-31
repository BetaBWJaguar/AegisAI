from abc import ABC, abstractmethod
from security.breach.infraction.infraction_result import InfractionResult
from security.breach.actions.actiondecision import ActionDecision


class InfractionService(ABC):

    @abstractmethod
    def analyze(self, text: str) -> InfractionResult:
        pass

    @abstractmethod
    def analyze_risk(self, text: str) -> tuple[str, float, bool]:
        pass

    @abstractmethod
    def decide_action(self, text: str) -> ActionDecision:
        pass
