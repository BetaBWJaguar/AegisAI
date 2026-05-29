# -*- coding: utf-8 -*-
import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth.authcontroller import get_current_user
from error.errortypes import ErrorType
from error.expectionhandler import ExpectionHandler
from profanity.escalation.escalation_service import EscalationService

logger = logging.getLogger(__name__)

router = APIRouter()
_escalation_service = EscalationService(config_file="config.json")

class ActionRulePayload(BaseModel):
    tier: int
    actions: list


@router.get("/state/{fingerprint}")
async def get_escalation_state(fingerprint: str, current_user=Depends(get_current_user)):
    state = _escalation_service.get_by_fingerprint(fingerprint)
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
    results = _escalation_service.list_all(limit=limit)
    return {"success": True, "count": len(results), "data": results}


@router.delete("/reset/{fingerprint}")
async def reset_escalation(fingerprint: str, current_user=Depends(get_current_user)):
    reset_ok = _escalation_service.reset(fingerprint)
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
    _escalation_service._rules_col.update_one(
        {"tier": payload.tier},
        {"$set": {"actions": payload.actions}},
        upsert=True
    )
    return {"success": True, "message": f"Tier {payload.tier} rules have been updated."}

@router.get("/rules/{tier}")
async def get_action_rule(tier: int, current_user=Depends(get_current_user)):
    rule = _escalation_service._rules_col.find_one({"tier": tier}, {"_id": 0})
    return {"success": True, "data": rule}
