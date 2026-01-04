from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auditmanager.auditlogserviceimpl import AuditLogServiceImpl
from error.errortypes import ErrorType
from error.expectionhandler import ExpectionHandler
from security.breach.infraction.infractionserviceimpl import InfractionServiceImpl
from user.userserviceimpl import UserServiceImpl
from workspace.workspaceserviceimpl import WorkspaceServiceImpl
from auth.authcontroller import get_current_user

router = APIRouter()
service = InfractionServiceImpl()
user_service = UserServiceImpl("config.json")
audit_log_service = AuditLogServiceImpl("config.json")
workspace_service = WorkspaceServiceImpl(user_service, audit_log_service)

def get_workspace_service():
    global workspace_service
    return workspace_service


class InfractionRequest(BaseModel):
    text: str


@router.post("/{user_id}/{workspace_id}/analyze")
def analyze_infraction(user_id: str, workspace_id: str, req: InfractionRequest, current_user=Depends(get_current_user)):
    if not req.text.strip():
        raise ExpectionHandler(
            message="Text cannot be empty",
            error_type=ErrorType.VALIDATION_ERROR
        )

    ws_service = get_workspace_service()
    if ws_service is None:
        raise ExpectionHandler(
            message="Workspace service not initialized",
            error_type=ErrorType.INTERNAL_SERVER_ERROR
        )

    workspace = ws_service.get_workspace(user_id, workspace_id)
    if workspace is None:
        raise ExpectionHandler(
            message="Workspace not found",
            error_type=ErrorType.NOT_FOUND
        )

    doxxing_settings = workspace.doxxing_settings
    if doxxing_settings is None:
        raise ExpectionHandler(
            message="Doxxing settings not found for this workspace",
            error_type=ErrorType.NOT_FOUND
        )

    result = service.analyze(req.text, doxxing_settings, workspace.language)
    decision = result.decision

    return {
        "violation": result.is_violation,
        "riskTier": result.risk_tier,
        "score": round(result.score, 4),
        "action": decision.action,
        "notifyUser": decision.notify_user,
        "notifyAdmin": decision.notify_admin,
        "maskContent": decision.mask_content,
        "logEvent": decision.log_event,
        "reason": decision.reason,
        "details": result.details
    }


@router.post("/{user_id}/{workspace_id}/risk-tier")
def analyze_risk_tier(user_id: str, workspace_id: str, req: InfractionRequest, current_user=Depends(get_current_user)):
    if not req.text.strip():
        raise ExpectionHandler(
            message="Text cannot be empty",
            error_type=ErrorType.VALIDATION_ERROR
        )

    ws_service = get_workspace_service()
    if ws_service is None:
        raise ExpectionHandler(
            message="Workspace service not initialized",
            error_type=ErrorType.INTERNAL_SERVER_ERROR
        )

    workspace = ws_service.get_workspace(user_id, workspace_id)
    if workspace is None:
        raise ExpectionHandler(
            message="Workspace not found",
            error_type=ErrorType.NOT_FOUND
        )

    doxxing_settings = workspace.doxxing_settings
    if doxxing_settings is None:
        raise ExpectionHandler(
            message="Doxxing settings not found for this workspace",
            error_type=ErrorType.NOT_FOUND
        )

    risk_tier, score, is_violation = service.analyze_risk(req.text, doxxing_settings, workspace.language)

    return {
        "violation": is_violation,
        "riskTier": risk_tier,
        "score": round(score, 4)
    }


@router.post("/{user_id}/{workspace_id}/decision")
def analyze_decision(user_id: str, workspace_id: str, req: InfractionRequest, current_user=Depends(get_current_user)):
    if not req.text.strip():
        raise ExpectionHandler(
            message="Text cannot be empty",
            error_type=ErrorType.VALIDATION_ERROR
        )

    ws_service = get_workspace_service()
    if ws_service is None:
        raise ExpectionHandler(
            message="Workspace service not initialized",
            error_type=ErrorType.INTERNAL_SERVER_ERROR
        )

    workspace = ws_service.get_workspace(user_id, workspace_id)
    if workspace is None:
        raise ExpectionHandler(
            message="Workspace not found",
            error_type=ErrorType.NOT_FOUND
        )

    doxxing_settings = workspace.doxxing_settings
    if doxxing_settings is None:
        raise ExpectionHandler(
            message="Doxxing settings not found for this workspace",
            error_type=ErrorType.NOT_FOUND
        )

    decision = service.decide_action(req.text, doxxing_settings, workspace.language)

    return {
        "action": decision.action,
        "notifyUser": decision.notify_user,
        "notifyAdmin": decision.notify_admin,
        "maskContent": decision.mask_content,
        "logEvent": decision.log_event,
        "reason": decision.reason
    }

