from typing import Dict, List, Optional
from abc import ABC, abstractmethod


class SynonymService(ABC):

    @abstractmethod
    def get_all_synonyms(self) -> Dict[str, List[str]]:
        pass

    @abstractmethod
    def get_synonym(self, word: str) -> Optional[List[str]]:
        pass

    @abstractmethod
    def add_synonym(self, word: str, synonyms: List[str]) -> bool:
        pass

    @abstractmethod
    def update_synonym(self, word: str, synonyms: List[str]) -> bool:
        pass

    @abstractmethod
    def delete_synonym(self, word: str) -> bool:
        pass

    @abstractmethod
    def add_synonyms_bulk(self, synonym_dict: Dict[str, List[str]]) -> bool:
        pass

    @abstractmethod
    def clear_all_synonyms(self) -> bool:
        pass
