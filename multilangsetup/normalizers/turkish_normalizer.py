import re
import unicodedata

class TurkishNormalizer:
    @staticmethod
    def normalize_characters(text: str) -> str:
        if not isinstance(text, str):
            return ""

        text = unicodedata.normalize("NFC", text)

        replacements = {
            "i̇": "i",
            "I": "ı",
            "İ": "i",
            "g": "g", "G": "G",
            "ş": "ş", "Ş": "Ş",
            "ç": "ç", "Ç": "Ç",
            "ö": "ö", "Ö": "Ö",
            "ü": "ü", "Ü": "Ü",
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

    @classmethod
    def normalize_all(cls, text: str) -> str:
        text = cls.normalize_characters(text)
        text = cls.normalize_spacing(text)
        text = cls.normalize_quotes(text)
        return text
