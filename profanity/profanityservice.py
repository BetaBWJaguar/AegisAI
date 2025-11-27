from abc import ABC, abstractmethod
from typing import Dict, Optional, List

class ProfanityService(ABC):

    @abstractmethod
    def detect(
            self,
            text: str,
            workspace_id,
            user_id: str,
            pipeline: Optional[List[str]] = None
    ) -> Dict:
        pass
