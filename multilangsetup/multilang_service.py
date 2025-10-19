from abc import ABC, abstractmethod
from typing import Optional, Dict

class MultiLangService(ABC):

    @abstractmethod
    def prepare(self, text: str, lang: Optional[str] = None) -> Dict:
        pass
