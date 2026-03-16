from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class ContentDecisionResponse(BaseModel):
    allowed: bool
    risk: Optional[str] = None
    action: Optional[str] = None
    reason: Optional[str] = None
    score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class BatchContentDecisionResponse(BaseModel):
    results: List[ContentDecisionResponse]
    total: int
    allowed_count: int
    blocked_count: int


class SpamSettingsResponse(BaseModel):
    enabled: bool
    rate_limit_count: int
    rate_limit_window_seconds: int
    duplicate_check: bool
    duplicate_reset_seconds: int
    burst_limit: int
    burst_window_seconds: int
    cooldown_seconds: int
    exempt_roles: List[str]
    max_message_length: int
    max_emojis: int
    max_repeated_char: int
    blocked_domains: List[str]
    allowed_domains: List[str]
    suspicious_tlds: List[str]


class ScoreThresholdsResponse(BaseModel):
    enabled: bool
    critical_threshold: float
    high_threshold: float
    medium_threshold: float


class ContentControlSettingsResponse(BaseModel):
    enabled: bool
    use_score_based_decision: bool
    spam: SpamSettingsResponse
    score_thresholds: ScoreThresholdsResponse
