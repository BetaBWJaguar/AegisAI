import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Any, Optional


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
    created_at: datetime
    updated_at: datetime
