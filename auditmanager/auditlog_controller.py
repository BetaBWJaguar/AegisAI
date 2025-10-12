from fastapi import APIRouter, Depends
from typing import List
import uuid

from auditmanager.acessmanager.user_access_service import UserAccessService
from auditmanager.auditlogserviceimpl import AuditLogServiceImpl
from auditmanager.create.create import AuditLogCreate
from auditmanager.response.response import AuditLogResponse
from error.errortypes import ErrorType
from error.expectionhandler import ExpectionHandler
from permcontrol.permissionscontrol import require_perm
from user.role import Role

router = APIRouter()
service = AuditLogServiceImpl()
access_service = UserAccessService(config_file="config.json")


@router.post(
    "/",
    response_model=AuditLogResponse,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
def create_audit_log(data: AuditLogCreate):
    log = service.create_log(**data.dict())
    return AuditLogResponse(**log.to_dict())


@router.get(
    "/workspace/{workspace_id}",
    response_model=List[AuditLogResponse]
)
def get_all_workspace_logs(workspace_id: uuid.UUID, user_id: uuid.UUID):
    access_service.verify_workspace_access(user_id, workspace_id)
    logs = service.get_all_logs(workspace_id)
    return [AuditLogResponse(**log.to_dict()) for log in logs]


@router.get(
    "/workspace/{workspace_id}/user/{user_id}",
    response_model=List[AuditLogResponse]
)
def get_user_logs(workspace_id: uuid.UUID, user_id: uuid.UUID):
    access_service.verify_workspace_access(user_id, workspace_id)
    logs = service.get_user_logs(user_id, workspace_id)
    return [AuditLogResponse(**log.to_dict()) for log in logs]


@router.get(
    "/workspace/{workspace_id}/log/{log_id}",
    response_model=AuditLogResponse
)
def get_log_by_id(workspace_id: uuid.UUID, log_id: uuid.UUID, user_id: uuid.UUID):
    try:
        access_service.verify_workspace_access(user_id, workspace_id)

        log = service.get_log_by_id(workspace_id, log_id)
        if not log:
            raise ExpectionHandler(
                message="Log not found.",
                error_type=ErrorType.NOT_FOUND,
                detail=f"Log with ID {log_id} not found in workspace {workspace_id}."
            )

        return AuditLogResponse(**log.to_dict())

    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to retrieve audit log.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )
