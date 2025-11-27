# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional

from auditmanager.auditlogserviceimpl import AuditLogServiceImpl
from auth.authcontroller import get_current_user
from profanity.profanityserviceimpl import ProfanityServiceImpl
from profanity.schemas.profanityrequest import DetectRequest
from profanity.schemas.profanityresponse import DetectResponse

from error.errortypes import ErrorType
from error.expectionhandler import ExpectionHandler
from user.userserviceimpl import UserServiceImpl
from workspace.workspaceserviceimpl import WorkspaceServiceImpl

router = APIRouter()
audit_log_service = AuditLogServiceImpl("config.json")
user_service = UserServiceImpl()
workspace_service = WorkspaceServiceImpl(user_service,audit_log_service)
profanity_service = ProfanityServiceImpl(workspace_service=workspace_service)


@router.post(
    "/detect",
    response_model=DetectResponse,
)
async def detect_text(data: DetectRequest,current_user=Depends(get_current_user)):
    try:
        if profanity_service is None:
            raise ExpectionHandler(
                message="Profanity service not initialized.",
                error_type=ErrorType.INTERNAL_SERVER_ERROR
            )

        result = profanity_service.detect(
            text=data.text,
            user_id=str(current_user.id),
            workspace_id=data.workspace_id,
            pipeline=data.pipeline
        )

        return DetectResponse(**result)

    except ValueError as e:
        raise ExpectionHandler(
            message="Invalid workspace or detection validation failed.",
            error_type=ErrorType.VALIDATION_ERROR,
            detail=str(e)
        )
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Unexpected error occurred during profanity detection.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/bulk",
)
async def detect_bulk(payload: Dict,current_user=Depends(get_current_user)):
    try:
        if profanity_service is None:
            raise ExpectionHandler(
                message="Profanity service not initialized.",
                error_type=ErrorType.INTERNAL_SERVER_ERROR
            )

        texts = payload.get("texts", [])
        workspace_id = payload.get("workspace_id")
        pipeline = payload.get("pipeline", None)

        if not texts or not isinstance(texts, list):
            raise ExpectionHandler(
                message="No texts provided for bulk analysis.",
                error_type=ErrorType.VALIDATION_ERROR
            )

        if pipeline:
            pipeline = [step for step in pipeline]

        results = []

        for original_text in texts:
            try:
                processed = profanity_service.detect(
                    text=original_text,
                    workspace_id=workspace_id,
                    pipeline=pipeline
                )
                results.append(processed)

            except Exception as e:
                results.append({
                    "text": original_text,
                    "error": str(e)
                })

        return JSONResponse(content={"count": len(results), "results": results})

    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to process bulk profanity detection.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
