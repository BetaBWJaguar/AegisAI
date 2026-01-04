import re
from security.breach.langs import tr, en

LANG_MAP = {
    "tr": tr,
    "en": en
}

RE_NAME_TITLE = re.compile(
    r"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]{2,}\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]{2,}\b"
)
RE_NAME_UPPER = re.compile(
    r"\b[A-ZÇĞİÖŞÜ]{3,}\s+[A-ZÇĞİÖŞÜ]{3,}\b"
)
RE_MENTION = re.compile(r"@\w{2,}")


class ContextDetector:
    @staticmethod
    def _get_lang(lang_code: str):
        return LANG_MAP.get(lang_code.lower(), tr)

    @staticmethod
    def _has_any(text: str, attr: str, lang_code: str = "tr") -> bool:
        t = text.lower()
        lang = ContextDetector._get_lang(lang_code)
        return any(
            hint in t
            for hint in getattr(lang, attr, [])
        )

    @staticmethod
    def has_person(text: str, lang_code: str = "tr") -> bool:
        if RE_MENTION.search(text):
            return True

        lang = ContextDetector._get_lang(lang_code)
        for regex in (RE_NAME_TITLE, RE_NAME_UPPER):
            for m in regex.finditer(text):
                phrase = m.group(0).lower()
                if not any(sw in phrase for sw in lang.ORG_STOPWORDS):
                    return True
        return False

    @staticmethod
    def has_target_reference(text: str, lang_code: str = "tr") -> bool:
        return ContextDetector._has_any(text, "TARGET_WORDS", lang_code)

    @staticmethod
    def has_address_hint(text: str, lang_code: str = "tr") -> bool:
        return ContextDetector._has_any(text, "ADDRESS_HINTS", lang_code)

    @staticmethod
    def has_expose_intent(text: str, lang_code: str = "tr") -> bool:
        return ContextDetector._has_any(text, "EXPOSE_INTENTS", lang_code)

    @staticmethod
    def is_self_disclosure(text: str, lang_code: str = "tr") -> bool:
        return ContextDetector._has_any(text, "SELF_DISCLOSURE_HINTS", lang_code)
    
    @staticmethod
    def has_vehicle_context(text: str, lang_code: str = "tr") -> bool:
        has_vehicle_word = ContextDetector._has_any(text, "VEHICLE_WORDS", lang_code)
        has_person = ContextDetector.has_person(text, lang_code)
        return has_vehicle_word and has_person


    @staticmethod
    def has_health_context(text: str, lang_code: str = "tr") -> bool:
        has_health_word = ContextDetector._has_any(text, "HEALTH_HINTS", lang_code)
        if not has_health_word:
            return False

        has_person = ContextDetector.has_person(text, lang_code)
        has_target = ContextDetector.has_target_reference(text, lang_code)

        return has_person or has_target
