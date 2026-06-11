from pydantic import BaseModel
from typing import Dict, List, Optional


class EscalationInfo(BaseModel):
    tier: int = 0
    label: str = "CLEAN"
    multiplier: float = 1.0
    total_infractions: int = 0


class PenaltyDurationInfo(BaseModel):
    total_duration_minutes: int = 0
    readable_duration: str = "0 minutes"
    penalties_count: int = 1
    escalation_multiplier: float = 1.0
    category_breakdown: Optional[Dict[str, int]] = None


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
    escalation: Optional[EscalationInfo] = None
    penalty_duration: Optional[PenaltyDurationInfo] = None
