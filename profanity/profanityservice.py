from abc import ABC, abstractmethod
from typing import Dict


class ProfanityService(ABC):

    @abstractmethod
    def detect(self, text: str, threshold: float) -> Dict:
        pass
