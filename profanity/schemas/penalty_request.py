# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field
from typing import Optional, List


class PenaltyItem(BaseModel):
    risk_level: str = Field(...)
    category: Optional[str] = Field(None)
    confidence: Optional[float] = Field(1.0, ge=0, le=1)


class CalculatePenaltyRequest(BaseModel):
    penalties: List[PenaltyItem] = Field(...)
    base_durations: Optional[dict] = Field(None)
    category_multipliers: Optional[dict] = Field(None)
    filter_by_risk_levels: Optional[List[str]] = Field(None)
    sort_by_confidence: Optional[bool] = Field(True)
    sort_descending: Optional[bool] = Field(True)
    include_category_stats: Optional[bool] = Field(False)
    escalation_multiplier: Optional[float] = Field(None, ge=1.0)
    ip: Optional[str] = Field(None)
    user_agent: Optional[str] = Field(None)
    accept_language: Optional[str] = Field(None)
