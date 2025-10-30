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
            "ş": "ş", "Ş": "Ş",
            "ç": "ç", "Ç": "Ç",
            "ö": "ö", "Ö": "Ö",
            "ü": "ü", "Ü": "Ü",
            "ğ": "ğ", "Ğ": "Ğ",
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
    def to_lower_turkish(text: str) -> str:
        if not isinstance(text, str):
            return ""
        trans_table = str.maketrans("Iİ", "ıi")
        return text.translate(trans_table).lower()

    @classmethod
    def normalize_all(cls, text: str, to_lower=True) -> str:
        text = cls.normalize_characters(text)
        text = cls.normalize_spacing(text)
        text = cls.normalize_quotes(text)
        if to_lower:
            text = cls.to_lower_turkish(text)
        return text.strip()
