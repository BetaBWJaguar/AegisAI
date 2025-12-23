import re

from security.breach.langs import tr, en

LANGS = [tr, en]

RE_TWO_CAPS = re.compile(r"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]{2,}\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]{2,}\b")
RE_MENTION = re.compile(r"@\w{2,}")

class ContextDetector:

    @staticmethod
    def has_person(text: str) -> bool:
        if RE_MENTION.search(text):
            return True

        for m in RE_TWO_CAPS.finditer(text):
            phrase = m.group(0).lower()
            for lang in LANGS:
                if not any(sw in phrase for sw in lang.ORG_STOPWORDS):
                    return True
        return False

    @staticmethod
    def has_address_hint(text: str) -> bool:
        t = text.lower()
        return any(
            hint in t
            for lang in LANGS
            for hint in lang.ADDRESS_HINTS
        )

    @staticmethod
    def has_expose_intent(text: str) -> bool:
        t = text.lower()
        return any(
            intent in t
            for lang in LANGS
            for intent in lang.EXPOSE_INTENTS
        )
