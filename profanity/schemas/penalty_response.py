# -*- coding: utf-8 -*-
from pydantic import BaseModel


class PenaltyDurationResponse(BaseModel):
    success: bool
    data: dict
