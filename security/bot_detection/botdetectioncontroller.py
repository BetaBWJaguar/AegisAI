from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from auth.authcontroller import get_current_user
from error.expectionhandler import ExpectionHandler
from permcontrol.permissionscontrol import require_perm
from user.role import Role

from security.bot_detection.botdetectionserviceimpl import BotDetectionServiceImpl
from security.bot_detection.schemas.bot_detection_request import (
    LogMessageRequest,
    CheckActorRequest,
    GetActorEventsRequest,
    ClearActorDataRequest
)
from security.bot_detection.schemas.bot_detection_response import (
    BotDetectionResponse,
    LogMessageResponse,
    ActorEventsResponse,
    ClearActorDataResponse
)

from error.errortypes import ErrorType

router = APIRouter()
service = BotDetectionServiceImpl()


@router.post(
    "/log",
    response_model=LogMessageResponse
)
async def log_message(
    request: LogMessageRequest
):
    try:
        service.log_message(request.actor_key)
        return LogMessageResponse(
            success=True,
            actor_key=request.actor_key,
            message="Message logged successfully"
        )
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to log message",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/check",
    response_model=BotDetectionResponse
)
async def check_actor(
    request: CheckActorRequest
):
    try:
        result = service.check_actor(request.actor_key)
        return BotDetectionResponse(**result)
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to analyze actor",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/events",
    response_model=ActorEventsResponse
)
async def get_actor_events(
    request: GetActorEventsRequest
):
    try:
        result = service.get_actor_events(request.actor_key)
        return ActorEventsResponse(**result)
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to retrieve actor events",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/clear",
    response_model=ClearActorDataResponse,
    dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))]
)
async def clear_actor_data(
    request: ClearActorDataRequest,
    current_user=Depends(get_current_user)
):
    try:
        success = service.clear_actor_data(request.actor_key)
        if not success:
            raise ExpectionHandler(
                message=f"No data found for actor: {request.actor_key}",
                error_type=ErrorType.NOT_FOUND
            )
        
        return ClearActorDataResponse(
            success=True,
            actor_key=request.actor_key,
            message="Actor data cleared successfully"
        )
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to clear actor data",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/check/{actor_key}",
    response_model=BotDetectionResponse
)
async def check_actor_by_path(
    actor_key: str
):
    try:
        result = service.check_actor(actor_key)
        return BotDetectionResponse(**result)
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to analyze actor",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/events/{actor_key}",
    response_model=ActorEventsResponse
)
async def get_actor_events_by_path(
    actor_key: str
):
    try:
        result = service.get_actor_events(actor_key)
        return ActorEventsResponse(**result)
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to retrieve actor events",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/clear/{actor_key}",
    response_model=ClearActorDataResponse,
    dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))]
)
async def clear_actor_data_by_path(
    actor_key: str,
    current_user=Depends(get_current_user)
):
    try:
        success = service.clear_actor_data(actor_key)
        if not success:
            raise ExpectionHandler(
                message=f"No data found for actor: {actor_key}",
                error_type=ErrorType.NOT_FOUND
            )
        
        return ClearActorDataResponse(
            success=True,
            actor_key=actor_key,
            message="Actor data cleared successfully"
        )
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to clear actor data",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )