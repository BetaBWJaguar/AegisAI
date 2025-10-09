from abc import ABC, abstractmethod
from typing import List, Dict

class ScrapperService(ABC):
    @abstractmethod
    def scrape_reddit(self, query: str, limit: int, subreddits: List[str]) -> List[Dict[str, str]]:
        pass

