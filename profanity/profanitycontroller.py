# -*- coding: utf-8 -*-
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional

from auditmanager.auditlogserviceimpl import AuditLogServiceImpl
from auth.authcontroller import get_current_user
from customrules.customrule_service_impl import CustomRuleServiceImpl
from profanity.escalation.escalation_service import EscalationService
from profanity.profanityserviceimpl import ProfanityServiceImpl
from profanity.schemas.profanityrequest import DetectRequest
from profanity.schemas.profanityresponse import DetectResponse

from error.errortypes import ErrorType
from error.expectionhandler import ExpectionHandler
from user.userserviceimpl import UserServiceImpl
from workspace.workspaceserviceimpl import WorkspaceServiceImpl

logger = logging.getLogger(__name__)

router = APIRouter()
audit_log_service = AuditLogServiceImpl("config.json")
user_service = UserServiceImpl()
workspace_service = WorkspaceServiceImpl(user_service, audit_log_service)
_custom_rule_service = CustomRuleServiceImpl(config_file="config.json")
profanity_service = ProfanityServiceImpl(
    workspace_service=workspace_service,
    rules_provider=lambda ws_id: _custom_rule_service.list_rules(
        workspace_id=ws_id, enabled_only=True,
    ),
)
_escalation_service = EscalationService(config_file="config.json")


_ESALATION_WORTHY_RISKS = {"MEDIUM", "HIGH", "CRITICAL"}


def _record_and_attach_escalation(
        result: dict,
        ip: Optional[str],
        user_agent: Optional[str],
        ignore_cooldown: bool = False
) -> dict:
    if not ip:
        result["escalation"] = None
        return result

    risk = result.get("risk", "LOW")
    category = result.get("predicted_label")
    confidence = result.get("confidence", 0.0)

    try:
        if risk in _ESALATION_WORTHY_RISKS:
            escalation_state = _escalation_service.record_infraction(
                ip=ip,
                risk_level=risk,
                category=category,
                confidence=confidence,
                user_agent=user_agent or "",
                ignore_cooldown=ignore_cooldown
            )
        else:
            escalation_state = _escalation_service.get_escalation_state(
                ip=ip,
                user_agent=user_agent or "",
            )

        result["escalation"] = {
            "tier": escalation_state["tier"],
            "label": escalation_state["label"],
            "multiplier": escalation_state["multiplier"],
            "total_infractions": escalation_state["total_infractions"],
        }
    except Exception:
        logger.exception("Failed to record escalation for ip=%s", ip)
        result["escalation"] = None

    return result


@router.post(
    "/detect",
    response_model=DetectResponse,
)
def detect_text(data: DetectRequest, current_user=Depends(get_current_user)):
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

        result = _record_and_attach_escalation(result, data.ip, data.user_agent)

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
def detect_bulk(payload: Dict, current_user=Depends(get_current_user)):
    try:
        if profanity_service is None:
            raise ExpectionHandler(
                message="Profanity service not initialized.",
                error_type=ErrorType.INTERNAL_SERVER_ERROR
            )

        texts = payload.get("texts", [])
        workspace_id = payload.get("workspace_id")
        pipeline = payload.get("pipeline", None)
        ip = payload.get("ip")
        user_agent = payload.get("user_agent")

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
                    user_id=str(current_user.id),
                    workspace_id=workspace_id,
                    pipeline=pipeline
                )
                processed = _record_and_attach_escalation(processed, ip, user_agent, ignore_cooldown=True)
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