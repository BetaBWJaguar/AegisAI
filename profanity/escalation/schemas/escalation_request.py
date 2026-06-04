# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field
from typing import Optional


class EscalationStateRequest(BaseModel):
    ip: str
    user_agent: Optional[str] = Field(None)
    accept_language: Optional[str] = Field(None)
    fingerprint: Optional[str] = Field(None)


class EscalationResetRequest(BaseModel):
    fingerprint: str


class EscalationListRequest(BaseModel):
    limit: int = Field(100, ge=1, le=1000)
