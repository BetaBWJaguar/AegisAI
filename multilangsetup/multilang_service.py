from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Sequence


class MultiLangService(ABC):

    @abstractmethod
    def prepare(self, text: str, lang: Optional[str] = None, pipeline: Optional[Sequence[str]] = None) -> Dict:
        pass