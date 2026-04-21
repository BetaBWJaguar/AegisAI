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
