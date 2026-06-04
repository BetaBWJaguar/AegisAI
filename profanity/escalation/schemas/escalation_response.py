# -*- coding: utf-8 -*-
from pydantic import BaseModel
from typing import Dict, List, Optional


class EscalationStateResponse(BaseModel):
    fingerprint: str
    ip: str
    total_infractions: int
    tier: int
    label: str
    multiplier: float
    category_breakdown: Dict[str, int]
    risk_breakdown: Dict[str, int]
    last_infraction_at: Optional[str]


class EscalationListResponse(BaseModel):
    success: bool
    count: int
    data: List[EscalationStateResponse]


class EscalationTierInfo(BaseModel):
    tier: int
    min_infractions: int
    multiplier: float
    label: str


class EscalationTierResponse(BaseModel):
    success: bool
    tiers: List[EscalationTierInfo]


class EscalationStatisticsResponse(BaseModel):
    success: bool
    data: dict
