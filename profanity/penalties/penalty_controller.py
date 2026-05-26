# -*- coding: utf-8 -*-
import logging
from fastapi import APIRouter, Depends
from typing import Dict, Optional

from auth.authcontroller import get_current_user
from profanity.escalation.escalation_service import EscalationService
from profanity.penalties.penalty_duration_service import PenaltyDurationService
from profanity.penalties.penalty_api_utils import (
    validate_penalties_list,
    format_penalty_response,
    filter_penalties_by_risk_level,
    sort_penalties_by_confidence,
    aggregate_penalties_by_category
)
from profanity.schemas.penalty_request import CalculatePenaltyRequest
from profanity.schemas.penalty_response import PenaltyDurationResponse

from error.errortypes import ErrorType
from error.expectionhandler import ExpectionHandler

logger = logging.getLogger(__name__)

router = APIRouter()
_escalation_service = EscalationService(config_file="config.json")


def _resolve_escalation_multiplier(request: CalculatePenaltyRequest) -> float:
    if request.escalation_multiplier is not None:
        return request.escalation_multiplier

    if request.ip:
        try:
            return _escalation_service.get_escalation_multiplier(
                ip=request.ip,
                user_agent=request.user_agent or "",
            )
        except Exception:
            logger.exception("Escalation lookup failed for ip=%s", request.ip)

    return 1.0


@router.post(
    "/calculate",
    response_model=PenaltyDurationResponse,
)
async def calculate_penalty_duration(request: CalculatePenaltyRequest, current_user=Depends(get_current_user)):
    penalties_data = [penalty.dict() for penalty in request.penalties]
    is_valid, error_message, valid_penalties = validate_penalties_list(penalties_data)

    if not is_valid:
        raise ExpectionHandler(
            message=error_message,
            error_type=ErrorType.VALIDATION_ERROR
        )

    filter_levels = request.filter_by_risk_levels
    if filter_levels:
        valid_penalties = filter_penalties_by_risk_level(valid_penalties, filter_levels)

    if request.sort_by_confidence:
        valid_penalties = sort_penalties_by_confidence(valid_penalties, request.sort_descending)

    base_durations = request.base_durations
    category_multipliers = request.category_multipliers

    penalty_service = PenaltyDurationService(
        base_durations=base_durations if base_durations is not None else {},
        category_multipliers=category_multipliers if category_multipliers is not None else {}
    )

    escalation_multiplier = _resolve_escalation_multiplier(request)
    result = penalty_service.calculate(valid_penalties, escalation_multiplier=escalation_multiplier)

    response_data = format_penalty_response(
        total_duration=result["total_duration_minutes"],
        penalties_count=len(valid_penalties)
    )

    if escalation_multiplier != 1.0:
        response_data["data"]["escalation_multiplier"] = escalation_multiplier

    if request.include_category_stats:
        response_data["data"]["category_stats"] = aggregate_penalties_by_category(valid_penalties)

    return PenaltyDurationResponse(**response_data)


@router.post(
    "/calculate/bulk",
)
async def calculate_penalty_duration_bulk(payload: Dict, current_user=Depends(get_current_user)):
    penalty_lists = payload.get("penalty_lists")

    if not isinstance(penalty_lists, list):
        raise ExpectionHandler(
            message="penalty_lists must be a list",
            error_type=ErrorType.VALIDATION_ERROR
        )

    if not penalty_lists:
        raise ExpectionHandler(
            message="penalty_lists cannot be empty",
            error_type=ErrorType.VALIDATION_ERROR
        )

    base_durations = payload.get("base_durations", {})
    category_multipliers = payload.get("category_multipliers", {})
    filter_by_risk_levels = payload.get("filter_by_risk_levels")
    sort_by_confidence = payload.get("sort_by_confidence", True)
    sort_descending = payload.get("sort_descending", True)
    include_category_stats = payload.get("include_category_stats", False)

    penalty_service = PenaltyDurationService(
        base_durations=base_durations,
        category_multipliers=category_multipliers
    )

    validate = validate_penalties_list
    filter_fn = filter_penalties_by_risk_level
    sort_fn = sort_penalties_by_confidence
    aggregate_fn = aggregate_penalties_by_category
    calculate = penalty_service.calculate
    append = list.append
    results = []

    for idx, penalties in enumerate(penalty_lists):
        try:
            is_valid, error_message, valid_penalties = validate(penalties)

            if not is_valid:
                append(results, {"index": idx, "error": error_message})
                continue

            if filter_by_risk_levels:
                valid_penalties = filter_fn(valid_penalties, filter_by_risk_levels)

            if sort_by_confidence:
                valid_penalties = sort_fn(valid_penalties, sort_descending)

            result = calculate(valid_penalties)

            result_data = {
                "index": idx,
                "total_duration_minutes": result["total_duration_minutes"],
                "penalties_count": len(valid_penalties)
            }

            if include_category_stats:
                result_data["category_stats"] = aggregate_fn(valid_penalties)

            append(results, result_data)

        except Exception as e:
            append(results, {"index": idx, "error": str(e)})

    return {
        "success": True,
        "total_requests": len(penalty_lists),
        "results": results
    }


@router.get(
    "/statistics",
)
async def get_penalty_statistics(
        base_durations: Optional[Dict] = None,
        category_multipliers: Optional[Dict] = None,
        current_user=Depends(get_current_user)
):
    penalty_service = PenaltyDurationService(
        base_durations=base_durations if base_durations is not None else {},
        category_multipliers=category_multipliers if category_multipliers is not None else {}
    )

    return penalty_service.get_statistics()