from abc import ABC, abstractmethod
from security.breach.infraction.infraction_result import InfractionResult


class InfractionService(ABC):

    @abstractmethod
    def analyze(self, text: str) -> InfractionResult:
        pass
