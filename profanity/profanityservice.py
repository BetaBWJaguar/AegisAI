from abc import ABC, abstractmethod
from typing import Dict, Optional, List

class ProfanityService(ABC):

    @abstractmethod
    def detect(
            self,
            text: str,
            threshold: float = None,
            pipeline: Optional[List[str]] = None
    ) -> Dict:
        pass
