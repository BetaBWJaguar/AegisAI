from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class MessageLevelMetadata:
    raw_text: str
    processed_text: str

    predicted_label: str
    confidence: float
    probabilities: Dict[str, float]

    risk: str

    masked: bool
    masked_text: Optional[str]
    mask_mode: Optional[str]

    advisory_action: Optional[str]
    policy_version: Optional[str]

    workspace_id: str
    user_id: str
    model_name: str
    model_version: str

    processed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "raw_text": self.raw_text,
            "processed_text": self.processed_text,
            "predicted_label": self.predicted_label,
            "confidence": round(self.confidence, 4),
            "probabilities": {
                k: round(v, 4) for k, v in self.probabilities.items()
            },
            "risk": self.risk,
            "masked": self.masked,
            "masked_text": self.masked_text,
            "mask_mode": self.mask_mode,
            "advisory_action": self.advisory_action,
            "policy_version": self.policy_version,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "processed_at": self.processed_at.isoformat()
        }
