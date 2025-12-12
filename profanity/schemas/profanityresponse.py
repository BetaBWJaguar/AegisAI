from pydantic import BaseModel
from typing import Dict, Optional


class DetectResponse(BaseModel):
    raw_text: str
    processed_text: str
    predicted_label: str
    confidence: float
    probabilities: Dict[str, float]
    risk: str
    masked: bool
    masked_text: Optional[str]
    mask_mode: Optional[str]
    blocked: bool
    visibility: Optional[str]
    threshold: Optional[float]
    advisory_action: Optional[str]
    policy_version: Optional[str]
    advisory_policy: Dict[str, str]
    workspace_id: str
    user_id: str
    model_name: str
    model_version: str
    processed_at: str
