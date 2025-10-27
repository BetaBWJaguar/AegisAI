import re
import langdetect

from multilangsetup.normalizers.turkish_normalizer import TurkishNormalizer

SUPPORTED_LANGUAGES = ["tr"]

class MultiLangProcessor:

    @staticmethod
    def normalize(text: str) -> str:
        if not isinstance(text, str):
            return ""
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def detect_language(text: str) -> str:
        try:
            lang = langdetect.detect(text)
            return lang.lower()
        except:
            return "unknown"

    @staticmethod
    def analyze_text_structure(text: str) -> dict:
        return {
            "char_count": len(text),
            "word_count": len(text.split()),
            "contains_numbers": any(ch.isdigit() for ch in text),
            "contains_emojis": bool(re.search(r"[\U0001F600-\U0001F64F]", text)),
            "contains_punctuation": bool(re.search(r"[^\w\s]", text))
        }

    @staticmethod
    def normalize_by_language(text: str, lang: str) -> str:
        if lang == "tr":
            text = TurkishNormalizer.normalize_all(text)
        return text
