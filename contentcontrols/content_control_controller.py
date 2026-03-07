from fastapi import APIRouter

from auditmanager.auditlogserviceimpl import AuditLogServiceImpl
from contentcontrols.content_control_serviceimpl import ContentControlServiceImpl
from contentcontrols.schemas.content_control_request import ContentEvaluateRequest
from contentcontrols.schemas.content_control_response import ContentDecisionResponse
from error.expectionhandler import ExpectionHandler
from error.errortypes import ErrorType
from user.userserviceimpl import UserServiceImpl
from workspace.workspaceserviceimpl import WorkspaceServiceImpl

router = APIRouter()

content_control_service = ContentControlServiceImpl()
user_service = UserServiceImpl()
auditlog = AuditLogServiceImpl(config_file="config.json")
workspace_service = WorkspaceServiceImpl(user_service,auditlog)


@router.post("/evaluate", response_model=ContentDecisionResponse)
async def evaluate_content(request: ContentEvaluateRequest):
    try:
        workspace = workspace_service.get_workspace(request.user_id,request.workspace_id)

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