from abc import ABC, abstractmethod
from typing import Dict, List, Any

class ReportBaseTemplate(ABC):
    template_name: str

    @abstractmethod
    def build(
            self,
            breakdown: Dict[str, Any],
            scenarios: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        pass
