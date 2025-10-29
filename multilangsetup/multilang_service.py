from abc import ABC, abstractmethod
from typing import Optional, Dict, List

class MultiLangService(ABC):

    @abstractmethod
    def prepare(self, text: str, lang: Optional[str] = None, pipeline: Optional[List[str]] = None) -> Dict:
        pass