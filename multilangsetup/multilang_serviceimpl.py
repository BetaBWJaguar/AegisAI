from typing import Optional, Dict
from multilangsetup.multilang_processor import MultiLangProcessor, SUPPORTED_LANGUAGES
from multilangsetup.multilang_service import MultiLangService


class MultiLangServiceImpl(MultiLangService):

    def prepare(self, text: str, lang: Optional[str] = None) -> Dict:
        normalized = MultiLangProcessor.normalize(text)

        if lang and lang.lower() != "auto":
            detected_lang = lang.lower()
        else:
            detected_lang = MultiLangProcessor.detect_language(normalized)

        language_supported = detected_lang in SUPPORTED_LANGUAGES

        language_normalized = MultiLangProcessor.normalize_by_language(normalized, detected_lang)

        analysis = MultiLangProcessor.analyze_text_structure(language_normalized)

        return {
            "raw_text": text,
            "normalized_text": language_normalized,
            "language": detected_lang if language_supported else "unknown",
            "language_supported": language_supported,
            "analysis": analysis,
            "ready_for_detection": True
        }
