from typing import Optional, Dict, Any, Sequence
from functools import lru_cache

from multilangsetup.multilang_processor import MultiLangProcessor, SUPPORTED_LANGUAGES
from multilangsetup.multilang_service import MultiLangService
from multilangsetup.multilang_step import Step

SORT_ORDER = [
    Step.NORMALIZE,
    Step.DETECT_LANGUAGE,
    Step.LANG_NORMALIZE,
    Step.ANALYZE,
    Step.KEYWORDS,
    Step.LINGUISTICS
]


class MultiLangServiceImpl(MultiLangService):

    @lru_cache(maxsize=1024)
    def prepare(self, text: str, lang: Optional[str] = None, pipeline: Optional[Sequence[str]] = None) -> Dict:

        if pipeline is None:
            pipeline = (
                Step.DETECT_LANGUAGE,
                Step.LANG_NORMALIZE,
                Step.ANALYZE,
                Step.KEYWORDS,
            )
        else:
            pipeline = [Step(p) for p in pipeline]

        pipeline = sorted(set(pipeline), key=lambda step: SORT_ORDER.index(step))

        result: Dict[str, Any] = {"raw_text": text}

        processed_text = MultiLangProcessor.normalize(text)

        detected_lang = "unknown"
        detection_info = None

        if Step.DETECT_LANGUAGE in pipeline:
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

        if Step.LANG_NORMALIZE in pipeline and language_supported:
            processed_text = MultiLangProcessor.normalize_by_language(processed_text, detected_lang)

        result["normalized_text"] = processed_text

        if Step.ANALYZE in pipeline:
            result["analysis"] = MultiLangProcessor.analyze_text_structure(processed_text)

        if Step.KEYWORDS in pipeline and language_supported:
            result["keywords"] = MultiLangProcessor.extract_keywords(processed_text, detected_lang)

        if Step.LINGUISTICS in pipeline and language_supported:
            result["linguistic_features"] = MultiLangProcessor.extract_linguistic_features(processed_text, detected_lang)

        result["ready_for_detection"] = True
        return result
