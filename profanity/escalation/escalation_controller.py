# -*- coding: utf-8 -*-
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator

from auth.authcontroller import get_current_user
from error.errortypes import ErrorType
from error.expectionhandler import ExpectionHandler
from profanity.escalation.escalation_service import EscalationService

logger = logging.getLogger(__name__)

router = APIRouter()

_escalation_service: Optional[EscalationService] = None

_VALID_ACTION_TYPES = {"LOG", "DB_UPDATE", "WEBHOOK"}


def _get_escalation_service() -> EscalationService:
    global _escalation_service
    if _escalation_service is None:
        _escalation_service = EscalationService(config_file="config.json")
    return _escalation_service



class ActionItem(BaseModel):
    type: str
    name: Optional[str] = None
    level: Optional[str] = None
    update_fields: Optional[dict] = None
    url: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[dict] = None
    payload_template: Optional[dict] = None

    @field_validator("type")
    @classmethod
    def validate_action_type(cls, v: str) -> str:
        normalized = v.upper()
        if normalized not in _VALID_ACTION_TYPES:
            raise ValueError(
                f"Invalid action type '{v}'. Must be one of {sorted(_VALID_ACTION_TYPES)}."
            )
        return normalized


class ActionRulePayload(BaseModel):
    tier: int
    actions: List[ActionItem]

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Tier must be a non-negative integer.")
        return v



@router.get("/state/{fingerprint}")
async def get_escalation_state(fingerprint: str, current_user=Depends(get_current_user)):
    svc = _get_escalation_service()
    state = svc.get_by_fingerprint(fingerprint)
    if not state:
        raise ExpectionHandler(
            message=f"No escalation record found for fingerprint: {fingerprint}",
            error_type=ErrorType.NOT_FOUND,
        )
    return {"success": True, "data": state}


@router.get("/list")
async def list_escalations(
    limit: int = 100,
    current_user=Depends(get_current_user),
):
    svc = _get_escalation_service()
    results = svc.list_all(limit=limit)
    return {"success": True, "count": len(results), "data": results}


@router.delete("/reset/{fingerprint}")
async def reset_escalation(fingerprint: str, current_user=Depends(get_current_user)):
    svc = _get_escalation_service()
    reset_ok = svc.reset(fingerprint)
    if not reset_ok:
        raise ExpectionHandler(
            message=f"No escalation record found for fingerprint: {fingerprint}",
            error_type=ErrorType.NOT_FOUND,
        )
    return {"success": True, "message": f"Escalation reset for {fingerprint}"}


@router.get("/tiers")
async def get_escalation_tiers(current_user=Depends(get_current_user)):
    from profanity.escalation.escalation_service import ESCALATION_TIERS
    return {"success": True, "tiers": ESCALATION_TIERS}

@router.post("/rules")
async def update_action_rule(payload: ActionRulePayload, current_user=Depends(get_current_user)):
    svc = _get_escalation_service()
    actions_raw = [action.model_dump(exclude_none=True) for action in payload.actions]
    svc.update_action_rule(payload.tier, actions_raw)
    return {"success": True, "message": f"Tier {payload.tier} rules have been updated."}


@router.get("/rules/{tier}")
async def get_action_rule(tier: int, current_user=Depends(get_current_user)):
    svc = _get_escalation_service()
    rule = svc.get_action_rule(tier)
    if not rule:
        raise ExpectionHandler(
            message=f"No action rule found for tier: {tier}",
            error_type=ErrorType.NOT_FOUND,
        )
    return {"success": True, "data": rule}
