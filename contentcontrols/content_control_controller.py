from fastapi import APIRouter, Depends

from auditmanager.auditlogserviceimpl import AuditLogServiceImpl
from contentcontrols.content_control_serviceimpl import ContentControlServiceImpl
from contentcontrols.schemas.content_control_request import ContentEvaluateRequest, BatchContentEvaluateRequest
from contentcontrols.schemas.content_control_response import (
    ContentDecisionResponse,
    BatchContentDecisionResponse,
    ContentControlSettingsResponse, ScoreThresholdsResponse, SpamSettingsResponse
)
from error.expectionhandler import ExpectionHandler
from error.errortypes import ErrorType
from permcontrol.permissionscontrol import require_perm
from user.role import Role
from user.userserviceimpl import UserServiceImpl
from workspace.workspaceserviceimpl import WorkspaceServiceImpl

router = APIRouter()

content_control_service = ContentControlServiceImpl()
user_service = UserServiceImpl()
auditlog = AuditLogServiceImpl(config_file="config.json")
workspace_service = WorkspaceServiceImpl(user_service, auditlog)


@router.post("/evaluate", response_model=ContentDecisionResponse)
async def evaluate_content(request: ContentEvaluateRequest):
    try:
        workspace = workspace_service.get_workspace(request.user_id, request.workspace_id)

        if not workspace:
            raise ValueError("Workspace not found")

        decision = content_control_service.evaluate_content(
            workspace=workspace,
            message=request.message,
            user_identifier=request.user_identifier,
            user_role=request.user_role
        )

        return ContentDecisionResponse(
            allowed=decision.allowed,
            risk=decision.risk,
            action=decision.action,
            reason=decision.reason,
            score=decision.score,
            metadata=decision.metadata
        )

    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while evaluating content.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/batch-evaluate", response_model=BatchContentDecisionResponse)
async def batch_evaluate_content(request: BatchContentEvaluateRequest):
    try:
        workspace = workspace_service.get_workspace(request.user_id, request.workspace_id)

        if not workspace:
            raise ValueError("Workspace not found")

        results = []
        allowed_count = 0
        blocked_count = 0

        for message in request.messages:
            decision = content_control_service.evaluate_content(
                workspace=workspace,
                message=message,
                user_identifier=request.user_identifier,
                user_role=request.user_role
            )

            decision_response = ContentDecisionResponse(
                allowed=decision.allowed,
                risk=decision.risk,
                action=decision.action,
                reason=decision.reason,
                score=decision.score,
                metadata=decision.metadata
            )

            results.append(decision_response)

            if decision.allowed:
                allowed_count += 1
            else:
                blocked_count += 1

        return BatchContentDecisionResponse(
            results=results,
            total=len(results),
            allowed_count=allowed_count,
            blocked_count=blocked_count
        )

    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while batch evaluating content.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/settings", response_model=ContentControlSettingsResponse)
async def get_content_control_settings(user_id: str, workspace_id: str):
    try:
        workspace = workspace_service.get_workspace(user_id, workspace_id)

        if not workspace:
            raise ValueError("Workspace not found")

        settings = workspace.content_control_settings

        return ContentControlSettingsResponse(
            enabled=settings.enabled,
            use_score_based_decision=settings.use_score_based_decision,

            spam=SpamSettingsResponse(
                enabled=settings.spam.enabled,
                rate_limit_count=settings.spam.rate_limit_count,
                rate_limit_window_seconds=settings.spam.rate_limit_window_seconds,
                duplicate_check=settings.spam.duplicate_check,
                duplicate_reset_seconds=settings.spam.duplicate_reset_seconds,
                burst_limit=settings.spam.burst_limit,
                burst_window_seconds=settings.spam.burst_window_seconds,
                cooldown_seconds=settings.spam.cooldown_seconds,
                exempt_roles=settings.spam.exempt_roles,
                max_message_length=settings.spam.max_message_length,
                max_emojis=settings.spam.max_emojis,
                max_repeated_char=settings.spam.max_repeated_char,
                blocked_domains=settings.spam.blocked_domains,
                allowed_domains=settings.spam.allowed_domains,
                suspicious_tlds=settings.spam.suspicious_tlds
            ),

            score_thresholds=ScoreThresholdsResponse(
                enabled=settings.score_thresholds.enabled,
                critical_threshold=settings.score_thresholds.critical_threshold,
                high_threshold=settings.score_thresholds.high_threshold,
                medium_threshold=settings.score_thresholds.medium_threshold
            )
        )

    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while retrieving content control settings.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/metrics/all",
            dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
async def get_all_metrics():
    try:
        return content_control_service.get_metrics().export_metrics()
    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while retrieving all metrics.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )