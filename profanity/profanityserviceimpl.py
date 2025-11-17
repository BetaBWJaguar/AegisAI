from typing import Dict
from transformers import BertTokenizerFast, BertForSequenceClassification
import torch

from profanity.profanityservice import ProfanityService


class ProfanityServiceImpl(ProfanityService):

    def __init__(self, model_path: str, threshold: float):
        self.threshold = threshold
        self.tokenizer = BertTokenizerFast.from_pretrained(model_path)
        self.model = BertForSequenceClassification.from_pretrained(model_path)

    def detect(self, text: str, threshold: float = None) -> Dict:
        if threshold is None:
            threshold = self.threshold

        inputs = self.tokenizer(text, return_tensors="pt")

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0].tolist()

        prob_clean, prob_offensive = probs
        label = "OFFENSIVE" if prob_offensive >= threshold else "CLEAN"

        return {
            "text": text,
            "clean_prob": round(prob_clean, 4),
            "offensive_prob": round(prob_offensive, 4),
            "label": label,
            "threshold": threshold
        }
