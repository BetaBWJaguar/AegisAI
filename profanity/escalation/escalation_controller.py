# -*- coding: utf-8 -*-
import logging
from typing import List, Optional, Any, Dict
from functools import lru_cache
from error.expectionhandler import ExpectionHandler

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator

from auth.authcontroller import get_current_user
from error.errortypes import ErrorType
from profanity.escalation.escalation_service import EscalationService, ESCALATION_TIERS
from profanity.escalation.schemas.escalation_request import (
    EscalationStateRequest,
    EscalationResetRequest,
    EscalationListRequest,
    EscalationCreateRequest,
    EscalationFilterRequest,
)
from profanity.escalation.schemas.escalation_response import (
    EscalationStateResponse,
    EscalationListResponse,
    EscalationTierResponse,
    EscalationStatisticsResponse, EscalationTierInfo,
)

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])

_VALID_ACTION_TYPES = {"LOG", "DB_UPDATE", "WEBHOOK"}


@lru_cache()
def get_escalation_service() -> EscalationService:
    return EscalationService(config_file="config.json")


class SuccessResponse(BaseModel):
    success: bool
    message: str


class ActionItem(BaseModel):
    type: str
    name: Optional[str] = None
    level: Optional[str] = None
    update_fields: Optional[Dict[str, Any]] = None
    url: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None
    payload_template: Optional[Dict[str, Any]] = None

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


@router.post("/state", response_model=EscalationStateResponse)
async def get_escalation_state_by_body(
        payload: EscalationStateRequest,
        svc: EscalationService = Depends(get_escalation_service),
):
    state = svc.get_escalation_state(
        ip=payload.ip,
        user_agent=payload.user_agent or "",
        accept_language=payload.accept_language or "",
        fingerprint=payload.fingerprint,
    )
    if not state:
        raise ExpectionHandler(
            message=f"No escalation record found for fingerprint: {payload.fingerprint}",
            error_type=ErrorType.NOT_FOUND,
        )
    return EscalationStateResponse(**state)


@router.get("/state/{fingerprint}", response_model=EscalationStateResponse)
async def get_escalation_state(
        fingerprint: str,
        svc: EscalationService = Depends(get_escalation_service)
):
    state = svc.get_by_fingerprint(fingerprint)
    if not state:
        raise ExpectionHandler(
            message=f"No escalation record found for fingerprint: {fingerprint}",
            error_type=ErrorType.NOT_FOUND,
        )
    return EscalationStateResponse(**state)


@router.get("/list", response_model=EscalationListResponse)
async def list_escalations(
        params: EscalationListRequest = Depends(),
        svc: EscalationService = Depends(get_escalation_service),
):
    results = svc.list_all(limit=params.limit)
    data = [EscalationStateResponse(**r) for r in results]
    return EscalationListResponse(success=True, count=len(data), data=data)


@router.post("/filter", response_model=EscalationListResponse)
async def filter_infractions(
        payload: EscalationFilterRequest,
        svc: EscalationService = Depends(get_escalation_service),
):
    if payload.category is None and payload.risk_level is None:
        raise ExpectionHandler(
            message="At least one of 'category' or 'risk_level' must be provided.",
            error_type=ErrorType.VALIDATION_ERROR,
        )
    results = svc.filter_infractions(
        category=payload.category,
        risk_level=payload.risk_level,
        limit=payload.limit,
    )
    data = [EscalationStateResponse(**r) for r in results]
    return EscalationListResponse(success=True, count=len(data), data=data)


@router.delete("/reset/{fingerprint}", response_model=SuccessResponse)
async def reset_escalation(
        fingerprint: str,
        svc: EscalationService = Depends(get_escalation_service),
):
    reset_ok = svc.reset(fingerprint)
    if not reset_ok:
        raise ExpectionHandler(
            message=f"No escalation record found for fingerprint: {fingerprint}",
            error_type=ErrorType.NOT_FOUND,
        )
    return SuccessResponse(success=True, message=f"Escalation reset for {fingerprint}")


@router.post("/reset", response_model=SuccessResponse)
async def reset_escalation_by_body(
        payload: EscalationResetRequest,
        svc: EscalationService = Depends(get_escalation_service),
):
    reset_ok = svc.reset(payload.fingerprint)
    if not reset_ok:
        raise ExpectionHandler(
            message=f"No escalation record found for fingerprint: {payload.fingerprint}",
            error_type=ErrorType.NOT_FOUND,
        )
    return SuccessResponse(success=True, message=f"Escalation reset for {payload.fingerprint}")


@router.get("/tiers", response_model=EscalationTierResponse)
async def get_escalation_tiers():
    return EscalationTierResponse(
        success=True,
        tiers=[EscalationTierInfo(**tier) for tier in ESCALATION_TIERS]
    )


@router.post("/rules", response_model=SuccessResponse)
async def update_action_rule(
        payload: ActionRulePayload,
        svc: EscalationService = Depends(get_escalation_service)
):
    actions_raw = [action.model_dump(exclude_none=True) for action in payload.actions]
    svc.update_action_rule(payload.tier, actions_raw)
    return SuccessResponse(success=True, message=f"Tier {payload.tier} rules have been updated.")


@router.get("/rules/{tier}", response_model=SuccessResponse)
async def get_action_rule(
        tier: int,
        svc: EscalationService = Depends(get_escalation_service)
):
    if tier < 0:
        raise ExpectionHandler(
            message="Tier must be a non-negative integer.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
        )
    rule = svc.get_action_rule(tier)
    if not rule:
        raise ExpectionHandler(
            message=f"No action rule found for tier: {tier}",
            error_type=ErrorType.NOT_FOUND,
        )
    return SuccessResponse(success=True, message=str(rule))


@router.post("/create", response_model=EscalationStateResponse)
async def create_escalation(
        payload: EscalationCreateRequest,
        svc: EscalationService = Depends(get_escalation_service),
):
    state = svc.create_escalation(
        user_id=payload.user_id,
        reason=payload.reason,
        level=payload.level,
        metadata=payload.metadata,
    )
    return EscalationStateResponse(**state)


@router.get("/statistics", response_model=EscalationStatisticsResponse)
async def get_escalation_statistics(
        svc: EscalationService = Depends(get_escalation_service)
):
    stats = svc.get_statistics()
    return EscalationStatisticsResponse(success=True, data=stats)