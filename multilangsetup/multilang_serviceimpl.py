from typing import Optional, Dict, Any, Sequence, Tuple
from functools import lru_cache

from multilangsetup.multilang_processor import MultiLangProcessor, SUPPORTED_LANGUAGES
from multilangsetup.multilang_service import MultiLangService
from multilangsetup.multilang_step import Step

class MultiLangServiceImpl(MultiLangService):

    def prepare(self, text: str, lang: Optional[str] = None, pipeline: Optional[Sequence[str]] = None) -> Dict:
        pipeline_tuple = tuple(pipeline) if isinstance(pipeline, list) else pipeline
        return self._prepare_cached(text, lang, pipeline_tuple)

    @lru_cache(maxsize=1024)
    def _prepare_cached(self, text: str, lang: Optional[str] = None, pipeline: Optional[Tuple[str, ...]] = None) -> Dict:
        if pipeline is None:
            pipeline = (
                Step.NORMALIZE,
                Step.DETECT_LANGUAGE,
                Step.LANG_NORMALIZE,
                Step.ANALYZE,
                Step.KEYWORDS,
                Step.LINGUISTICS
            )

        result: Dict[str, Any] = { "raw_text": text, "errors": {}, "steps_executed": [] }
        processed_text = text
        detected_lang = lang.lower() if lang else "auto"
        detection_info = None

        if Step.NORMALIZE in pipeline:
            try:
                processed_text = MultiLangProcessor.normalize(processed_text)
                result["steps_executed"].append(Step.NORMALIZE.value)
            except Exception as e:
                result["errors"][Step.NORMALIZE.value] = str(e)

        if detected_lang == "auto" and Step.DETECT_LANGUAGE in pipeline:
            try:
                if lang and lang.lower() != "auto":
                    detected_lang = lang.lower()
                    detection_info = {"lang": detected_lang, "confidence": 1.0, "source": "user_provided"}
                else:
                    detection_info = MultiLangProcessor.detect_language(processed_text)
                    if detection_info and detection_info.get("lang"):
                        detected_lang = detection_info["lang"]
                    else:
                        detected_lang = "unknown"
                        detection_info = {"lang": "unknown", "confidence": 0.0, "source": "detection_failed"}

                result["language_detection"] = detection_info
                result["steps_executed"].append(Step.DETECT_LANGUAGE.value)
            except Exception as e:
                result["errors"][Step.DETECT_LANGUAGE.value] = str(e)
                detected_lang = "unknown"
        elif lang:
            detected_lang = lang.lower()

        for step in pipeline:
            if step.value in result["steps_executed"]:
                continue

            try:

                if step == Step.LANG_NORMALIZE:
                    if detected_lang in SUPPORTED_LANGUAGES:
                        processed_text = MultiLangProcessor.normalize_by_language(processed_text, detected_lang)

                elif step == Step.ANALYZE:
                    result["analysis"] = MultiLangProcessor.analyze_text_structure(processed_text)

                elif step == Step.KEYWORDS:
                    if detected_lang in SUPPORTED_LANGUAGES:
                        result["keywords"] = MultiLangProcessor.extract_keywords(processed_text, detected_lang)

                elif step == Step.LINGUISTICS:
                    if detected_lang in SUPPORTED_LANGUAGES:
                        result["linguistic_features"] = MultiLangProcessor.extract_linguistic_features(processed_text, detected_lang)

                result["steps_executed"].append(step.value)

            except Exception as e:
                result["errors"][step.value] = str(e)

        result["normalized_text"] = processed_text
        result["language"] = detected_lang if detected_lang in SUPPORTED_LANGUAGES else "unknown"
        result["language_supported"] = detected_lang in SUPPORTED_LANGUAGES
        result["ready_for_detection"] = True

        return result