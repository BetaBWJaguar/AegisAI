from abc import ABC, abstractmethod
from typing import List, Dict
import re
import html
import unicodedata

class ScrapperBase(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def fetch(self, query: str, limit: int = 50) -> List[Dict[str, str]]:
        pass

    def clean_text(self, text: str) -> str:
        text = html.unescape(text)
        text = unicodedata.normalize("NFKD", text)
        text = re.sub(r"http\S+", "", text)
        text = re.sub(r"@\w+", "", text)
        text = re.sub(r"#[A-Za-z0-9_]+", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
