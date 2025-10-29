import re
import unicodedata


class ObfuscationHelper:

    @staticmethod
    def normalize_unicode(text: str) -> str:
        return unicodedata.normalize("NFC", text)

    @staticmethod
    def clean_redundant_symbols(text: str) -> str:
        text = re.sub(r'([!?.*#@%&])\1{2,}', r'\1', text)
        text = re.sub(r'\s{2,}', ' ', text)
        return text.strip()
