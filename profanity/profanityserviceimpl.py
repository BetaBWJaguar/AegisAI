from typing import Dict, Optional
import torch
from transformers import BertTokenizerFast, BertForSequenceClassification

from logs.predictionlogmanager import PredictionLogger
from profanity.maskingrules.maskingruleautomation import MaskingRuleAutomation
from profanity.messagelevelmetadata import MessageLevelMetadata
from profanity.profanityservice import ProfanityService
from profanity.categories.profanity_label_validator import ProfanityLabelValidator
from multilangsetup.multilang_step import Step
from multilangsetup.multilang_processor import MultiLangProcessor, SUPPORTED_LANGUAGES
from multilangsetup.obsfucationresolver.obsfucation_resolver import ObfuscationResolver
from trainer.modelregistry import ModelRegistry


class ProfanityServiceImpl(ProfanityService):

    def __init__(self, workspace_service, model_root: str = "models", label_validator: Optional[ProfanityLabelValidator] = None):
        self.workspace_service = workspace_service
        self.model_root = model_root
        self.registry = ModelRegistry()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_cache = {}
        self.tokenizer_cache = {}
        self.label_validator = label_validator

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

    def detect(
            self,
            text: str,
            user_id: str,
            workspace_id: str,
            pipeline: Optional[list] = None
    ):

        workspace = self.workspace_service.get_workspace(user_id, workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")

        lang = workspace.language.lower()
        model_name = workspace.model_name
        if not model_name:
            raise ValueError(f"Workspace {workspace_id} has no model_name defined.")

        tokenizer, model, model_path = self._load_model(
            model_name=model_name,
            model_version=workspace.model_version
        )

        if pipeline is None:
            pipeline = self.default_pipeline
        else:
            pipeline = [
                Step(p) if isinstance(p, str) else p
                for p in pipeline
            ]

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
        predicted_label = model.config.id2label.get(
            predicted_id, f"class_{predicted_id}"
        )
        confidence = float(probs[predicted_id])

        if self.label_validator and not self.label_validator.validate_label(predicted_label):
            raise ValueError(
                f"Invalid predicted label '{predicted_label}'. "
                f"Label does not match known profanity categories."
            )

        PredictionLogger.log(text, predicted_label, confidence)

        mask_meta = MaskingRuleAutomation.apply_if_needed(
            text=text,
            workspace=workspace,
            predicted_label=predicted_label,
            confidence=confidence
        )

        advisory = mask_meta.get("advisory", {})

        metadata = MessageLevelMetadata(
            raw_text=text,
            processed_text=processed,
            predicted_label=predicted_label,
            confidence=confidence,
            probabilities={
                model.config.id2label[i]: float(p)
                for i, p in enumerate(probs)
            },
            risk=mask_meta.get("risk", "LOW"),
            masked=mask_meta.get("masked", False),
            masked_text=mask_meta.get("masked_text"),
            mask_mode=mask_meta.get("mode"),
            blocked=mask_meta.get("blocked", False),
            visibility=mask_meta.get("visibility"),
            threshold=mask_meta.get("threshold"),
            advisory_action=advisory.get("suggested_action"),
            policy_version=advisory.get("policy_version"),
            advisory_policy=mask_meta.get("advisory_policy", {}),
            workspace_id=workspace_id,
            user_id=user_id,
            model_name=model_name,
            model_version=workspace.model_version
        )

        return metadata.to_dict()

