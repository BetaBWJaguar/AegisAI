import re
import langdetect

SUPPORTED_LANGUAGES = ["tr", "en"]

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
