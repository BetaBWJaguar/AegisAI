# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Optional

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

router = APIRouter()


@router.post(
    "/calculate",
    response_model=PenaltyDurationResponse,
)
async def calculate_penalty_duration(request: CalculatePenaltyRequest):
    try:
        penalties_data = [penalty.dict() for penalty in request.penalties]
        is_valid, error_message, valid_penalties = validate_penalties_list(penalties_data)
        
        if not is_valid:
            raise ExpectionHandler(
                message=error_message,
                error_type=ErrorType.VALIDATION_ERROR
            )
        
        if request.filter_by_risk_levels:
            valid_penalties = filter_penalties_by_risk_level(valid_penalties, request.filter_by_risk_levels)
        
        if request.sort_by_confidence:
            valid_penalties = sort_penalties_by_confidence(valid_penalties, request.sort_descending)

        base_durations = request.base_durations if request.base_durations is not None else {}
        category_multipliers = request.category_multipliers if request.category_multipliers is not None else {}
        
        penalty_service = PenaltyDurationService(
            base_durations=base_durations,
            category_multipliers=category_multipliers
        )

        result = penalty_service.calculate(valid_penalties)
        
        response_data = format_penalty_response(
            total_duration=result["total_duration_minutes"],
            penalties_count=len(valid_penalties)
        )
        
        if request.include_category_stats:
            category_stats = aggregate_penalties_by_category(valid_penalties)
            response_data["data"]["category_stats"] = category_stats

        return PenaltyDurationResponse(**response_data)

    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Unexpected error occurred during penalty calculation.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/calculate/bulk",
)
async def calculate_penalty_duration_bulk(payload: Dict):
    try:
        penalty_lists = payload.get("penalty_lists", [])
        
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

        results = []
        
        for idx, penalties in enumerate(penalty_lists):
            try:
                is_valid, error_message, valid_penalties = validate_penalties_list(penalties)
                
                if not is_valid:
                    results.append({
                        "index": idx,
                        "error": error_message
                    })
                    continue
                
                if filter_by_risk_levels:
                    valid_penalties = filter_penalties_by_risk_level(valid_penalties, filter_by_risk_levels)
                
                if sort_by_confidence:
                    valid_penalties = sort_penalties_by_confidence(valid_penalties, sort_descending)
                
                result = penalty_service.calculate(valid_penalties)
                
                result_data = {
                    "index": idx,
                    "total_duration_minutes": result["total_duration_minutes"],
                    "penalties_count": len(valid_penalties)
                }
                
                if include_category_stats:
                    category_stats = aggregate_penalties_by_category(valid_penalties)
                    result_data["category_stats"] = category_stats
                
                results.append(result_data)
                
            except Exception as e:
                results.append({
                    "index": idx,
                    "error": str(e)
                })

        return {
            "success": True,
            "total_requests": len(penalty_lists),
            "results": results
        }

    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to process bulk penalty calculation.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/statistics",
)
async def get_penalty_statistics(
    base_durations: Optional[Dict] = None,
    category_multipliers: Optional[Dict] = None
):
    try:
        base_durations = base_durations if base_durations is not None else {}
        category_multipliers = category_multipliers if category_multipliers is not None else {}

        penalty_service = PenaltyDurationService(
            base_durations=base_durations,
            category_multipliers=category_multipliers
        )

        return penalty_service.get_statistics()

    except Exception as e:
        raise ExpectionHandler(
            message="Failed to retrieve penalty statistics.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
