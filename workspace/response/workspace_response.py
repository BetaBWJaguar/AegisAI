import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class SpamSettingsResponse(BaseModel):
    enabled: bool
    rate_limit_count: int
    rate_limit_window_seconds: int
    duplicate_check: bool
    duplicate_reset_seconds: int
    burst_limit: int
    cooldown_seconds: int


class ContentControlSettingsResponse(BaseModel):
    enabled: bool
    spam: SpamSettingsResponse


class DoxxingPIIConfigResponse(BaseModel):
    enabled: bool
    weight: Optional[float] = None


class DoxxingContextConfigResponse(BaseModel):
    enabled: bool
    weight: Optional[float] = None


class DoxxingSettingsResponse(BaseModel):
    enabled: bool
    threshold: float
    pii_config: Dict[str, DoxxingPIIConfigResponse] = {}
    context_config: Dict[str, DoxxingContextConfigResponse] = {}
    detect_social_media: bool
    allow_self_disclosure: bool
    self_disclosure_penalty: float
    risk_actions: Dict[str, str]
    notify_user: bool
    notify_admin: bool
    log_violations: bool
    mask_content: bool


class RuleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    type: str
    params: Dict[str, Any]

class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    model_id: str
    model_name: str
    model_version: Optional[str] = None
    language: str
    bot_detection: bool
    rules: List[RuleResponse] = []
    censor_settings: Dict[str, Any] = {}
    doxxing_settings: DoxxingSettingsResponse
    content_control_settings: ContentControlSettingsResponse
    created_at: datetime
    updated_at: datetime
