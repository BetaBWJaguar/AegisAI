from typing import Dict, Optional
import torch
from transformers import BertTokenizerFast, BertForSequenceClassification

from logs.predictionlogmanager import PredictionLogger
from profanity.profanityservice import ProfanityService
from multilangsetup.multilang_step import Step
from multilangsetup.multilang_processor import MultiLangProcessor, SUPPORTED_LANGUAGES
from multilangsetup.obsfucationresolver.obsfucation_resolver import ObfuscationResolver


class ProfanityServiceImpl(ProfanityService):

    def __init__(self, model_path: str):
        self.tokenizer = BertTokenizerFast.from_pretrained(model_path)
        self.model = BertForSequenceClassification.from_pretrained(model_path)
        self.labels = self.model.config.id2label

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

        self.default_pipeline = [
            Step.NORMALIZE,
            Step.LANG_NORMALIZE
        ]

    def detect(self, text: str, workspace_language: str,
               pipeline: Optional[list] = None) -> Dict:

        pipeline = pipeline or self.default_pipeline
        processed = text

        if Step.NORMALIZE in pipeline:
            processed = MultiLangProcessor.normalize(processed)

        lang = workspace_language.lower()

        if Step.LANG_NORMALIZE in pipeline:
            if lang in SUPPORTED_LANGUAGES:
                processed = MultiLangProcessor.normalize_by_language(processed, lang)

            processed = ObfuscationResolver.resolve_all(processed, lang=lang)

        inputs = self.tokenizer(processed, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs_tensor = torch.softmax(outputs.logits, dim=-1)[0]

        probs = probs_tensor.tolist()

        predicted_id = int(torch.argmax(probs_tensor))
        predicted_label = self.labels.get(predicted_id, f"class_{predicted_id}")

        PredictionLogger.log(text, predicted_label, probs[predicted_id])

        return {
            "raw_text": text,
            "processed_text": processed,
            "workspace_language": lang,
            "probabilities": {
                self.labels[i]: round(float(p), 4) for i, p in enumerate(probs)
            },
            "predicted_label": predicted_label,
            "steps_executed": [s.value for s in pipeline]
        }
