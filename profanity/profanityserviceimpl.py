from typing import Dict, Optional
import torch
from transformers import BertTokenizerFast, BertForSequenceClassification

from logs.predictionlogmanager import PredictionLogger
from profanity.profanityservice import ProfanityService
from multilangsetup.multilang_step import Step
from multilangsetup.multilang_processor import MultiLangProcessor, SUPPORTED_LANGUAGES
from multilangsetup.obsfucationresolver.obsfucation_resolver import ObfuscationResolver
from trainer.modelregistry import ModelRegistry


class ProfanityServiceImpl(ProfanityService):

    def __init__(self, workspace_service, model_root: str = "models"):
        self.workspace_service = workspace_service
        self.model_root = model_root
        self.registry = ModelRegistry()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_cache = {}
        self.tokenizer_cache = {}

        self.default_pipeline = [
            Step.NORMALIZE,
            Step.LANG_NORMALIZE
        ]

    def _load_model(self, model_name: str, model_version: str):
        model_doc = self.registry.get_model(model_name, model_version)

        if not model_doc:
            raise ValueError(f"Model {model_name} v{model_version} not found in Model Registry")

        model_path = model_doc["model_path"]

        if model_path in self.model_cache:
            return (
                self.tokenizer_cache[model_path],
                self.model_cache[model_path],
                model_path
            )

        tokenizer = BertTokenizerFast.from_pretrained(model_path)
        model = BertForSequenceClassification.from_pretrained(model_path)
        model.to(self.device)

        self.model_cache[model_path] = model
        self.tokenizer_cache[model_path] = tokenizer

        return tokenizer, model, model_path

    def detect(self, text: str, user_id: str, workspace_id: str, pipeline: Optional[list] = None):

        workspace = self.workspace_service.get_workspace(user_id, workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")

        lang = workspace.language.lower()
        model_name = workspace.model_name
        if not model_name:
            raise ValueError(f"Workspace {workspace_id} has no model_name defined.")

        tokenizer, model, model_path = self._load_model(
            model_name=workspace.model_name,
            model_version=workspace.model_version
        )

        if pipeline is None:
            pipeline = self.default_pipeline
        elif isinstance(pipeline, list) and len(pipeline) == 0:
            pipeline = []
        else:
            pipeline = [Step(p) if isinstance(p, str) else p for p in pipeline]

        processed = text

        if Step.NORMALIZE in pipeline:
            processed = MultiLangProcessor.normalize(processed)

        if Step.LANG_NORMALIZE in pipeline:
            if lang in SUPPORTED_LANGUAGES:
                processed = MultiLangProcessor.normalize_by_language(processed, lang)
            processed = ObfuscationResolver.resolve_all(processed, lang=lang)


        inputs = tokenizer(processed, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            probs_tensor = torch.softmax(outputs.logits, dim=-1)[0]

        probs = probs_tensor.tolist()
        predicted_id = int(torch.argmax(probs_tensor))
        predicted_label = model.config.id2label.get(predicted_id, f"class_{predicted_id}")

        PredictionLogger.log(text, predicted_label, probs[predicted_id])

        return {
            "raw_text": text,
            "processed_text": processed,
            "workspace_id": workspace_id,
            "workspace_language": lang,
            "model_name_used": model_name,
            "model_path_used": model_path,
            "probabilities": {
                model.config.id2label[i]: round(float(p), 4) for i, p in enumerate(probs)
            },
            "predicted_label": predicted_label,
            "steps_executed": [s.value for s in pipeline]
        }
