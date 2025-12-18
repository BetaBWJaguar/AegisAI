import math
import re
from collections import Counter

import unicodedata

class EnglishNormalizer:
    @staticmethod
    def normalize_characters(text: str) -> str:
        if not isinstance(text, str):
            return ""

        text = unicodedata.normalize("NFC", text)

        replacements = {
            "–": "-",
            "—": "-",
            "…": "...",
            "“": '"', "”": '"',
            "‘": "'", "’": "'",
            "´": "'",
        }
        for k, v in replacements.items():
            text = text.replace(k, v)

        return text

    @staticmethod
    def normalize_spacing(text: str) -> str:
        text = re.sub(r"\s+", " ", text)

        text = re.sub(r"\s+([,.!?;:])", r"\1", text)

        text = re.sub(r"([,.!?;:])([^\s])", r"\1 \2", text)

        return text.strip()

    @staticmethod
    def normalize_quotes(text: str) -> str:
        text = text.replace("“", '"').replace("”", '"')
        text = text.replace("‘", "'").replace("’", "'")
        return text

    @staticmethod
    def clean_unnecessary_punctuation(text: str) -> str:
        if not isinstance(text, str):
            return ""

        text = re.sub(r'([!?.,;:])\1{2,}', r'\1\1', text)

        text = re.sub(r'\b([!?.,;:]+)([a-zA-Z])', r'\2', text)

        text = re.sub(r'\(\s*([.,;:!?]+)\s*\)', '(', text)
        text = re.sub(r'\[\s*([.,;:!?]+)\s*\]', '[', text)

        text = re.sub(r'([.,;:!?])\s*"', r'"\1', text)
        text = re.sub(r'"\s*([.,;:!?])', r'\1"', text)
        
        return text

    @staticmethod
    def normalize_repeated_letters(text: str) -> str:
        if not isinstance(text, str):
            return ""

        text = re.sub(r'([a-zA-Z])\1{2,}', r'\1\1', text)
        
        return text

    @staticmethod
    def to_lower(text: str) -> str:
        if not isinstance(text, str):
            return ""
        return text.lower()

    @staticmethod
    def calculate_entropy(text: str) -> float:
        if not isinstance(text, str) or not text:
            return 0.0

        counts = Counter(text)
        total = len(text)

        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)

        return round(entropy, 4)


    @classmethod
    def normalize_all(cls, text: str, to_lower=True) -> str:
        text = cls.normalize_characters(text)
        text = cls.clean_unnecessary_punctuation(text)
        text = cls.normalize_spacing(text)
        text = cls.normalize_quotes(text)
        text = cls.normalize_repeated_letters(text)
        if to_lower:
            text = cls.to_lower(text)
        return text.strip()
