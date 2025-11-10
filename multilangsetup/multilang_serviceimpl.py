from typing import Optional, Dict, List, Any, Sequence
from functools import lru_cache

from multilangsetup.multilang_processor import MultiLangProcessor, SUPPORTED_LANGUAGES
from multilangsetup.multilang_service import MultiLangService

class MultiLangServiceImpl(MultiLangService):

    @lru_cache(maxsize=1024)
    def prepare(self, text: str, lang: Optional[str] = None, pipeline: Optional[Sequence[str]] = None) -> Dict:

        if pipeline is None:
            pipeline = ('detect_language', 'lang_normalize', 'analyze', 'keywords')
        else:
            pipeline = tuple(pipeline)

        result: Dict[str, Any] = {"raw_text": text}

        processed_text = text

        detected_lang = "unknown"
        if 'detect_language' in pipeline:
            if lang and lang.lower() != "auto":
                detected_lang = lang.lower()
                detection_info = {"lang": detected_lang, "confidence": 1.0, "source": "user_provided"}
            else:
                detection_info = MultiLangProcessor.detect_language(processed_text)
                detected_lang = detection_info["lang"]

            result["language_detection"] = detection_info

        language_supported = detected_lang in SUPPORTED_LANGUAGES
        result["language"] = detected_lang if language_supported else "unknown"
        result["language_supported"] = language_supported

        if 'lang_normalize' in pipeline and language_supported:
            processed_text = MultiLangProcessor.normalize_by_language(processed_text, detected_lang)
            result["normalized_text"] = processed_text
        else:
            result["normalized_text"] = processed_text

        if 'analyze' in pipeline:
            analysis = MultiLangProcessor.analyze_text_structure(processed_text)
            result["analysis"] = analysis

        if 'linguistics' in pipeline and language_supported:
            linguistic_features = MultiLangProcessor.extract_linguistic_features(processed_text, detected_lang)
            result["linguistic_features"] = linguistic_features

        if 'keywords' in pipeline and language_supported:
            keywords = MultiLangProcessor.extract_keywords(processed_text, detected_lang)
            result["keywords"] = keywords

        result["ready_for_detection"] = True
        return result