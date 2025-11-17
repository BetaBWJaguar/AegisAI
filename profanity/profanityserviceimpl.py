from typing import Dict, Optional
import torch
from transformers import BertTokenizerFast, BertForSequenceClassification

from profanity.profanityservice import ProfanityService
from multilangsetup.multilang_step import Step
from multilangsetup.multilang_processor import MultiLangProcessor, SUPPORTED_LANGUAGES
from multilangsetup.obsfucationresolver.obsfucation_resolver import ObfuscationResolver


class ProfanityServiceImpl(ProfanityService):

    def __init__(self, model_path: str, threshold: float):
        self.threshold = threshold
        self.tokenizer = BertTokenizerFast.from_pretrained(model_path)
        self.model = BertForSequenceClassification.from_pretrained(model_path)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

        self.default_pipeline = [
            Step.NORMALIZE,
            Step.DETECT_LANGUAGE,
            Step.LANG_NORMALIZE
        ]

    def detect(self, text: str, threshold: Optional[float] = None,
               pipeline: Optional[list] = None) -> Dict:

        if threshold is None:
            threshold = self.threshold

        pipeline = pipeline or self.default_pipeline

        processed = text
        detected_lang = None
        lang_info = None

        if Step.NORMALIZE in pipeline:
            processed = MultiLangProcessor.normalize(processed)

        if Step.DETECT_LANGUAGE in pipeline:
            lang_info = MultiLangProcessor.detect_language(processed)
            detected_lang = lang_info.get("lang", "unknown")
        else:
            detected_lang = "unknown"


        if Step.LANG_NORMALIZE in pipeline:
            if detected_lang in SUPPORTED_LANGUAGES:
                processed = MultiLangProcessor.normalize_by_language(processed, detected_lang)

            processed = ObfuscationResolver.resolve_all(processed, lang=detected_lang)

        model_inputs = self.tokenizer(processed, return_tensors="pt")
        model_inputs = {k: v.to(self.device) for k, v in model_inputs.items()}

        with torch.no_grad():
            outputs = self.model(**model_inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0].tolist()

        prob_clean, prob_offensive = probs
        label = "OFFENSIVE" if prob_offensive >= threshold else "CLEAN"

        return {
            "raw_text": text,
            "processed_text": processed,

            "language": detected_lang,
            "language_detection": lang_info,
            "language_supported": detected_lang in SUPPORTED_LANGUAGES,

            "clean_prob": round(prob_clean, 4),
            "offensive_prob": round(prob_offensive, 4),
            "label": label,
            "threshold": threshold,

            "steps_executed": [s.value for s in pipeline]
        }
