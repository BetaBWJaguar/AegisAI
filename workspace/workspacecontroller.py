from fastapi import APIRouter, HTTPException, Depends
from typing import List

from auditmanager.auditlogserviceimpl import AuditLogServiceImpl
from auth.authcontroller import get_current_user
from error.errortypes import ErrorType
from error.expectionhandler import ExpectionHandler
from user.violations import Violation
from user.workspace import Workspace
from user.rule import Rule
from user.userserviceimpl import UserServiceImpl
from workspace.workspaceserviceimpl import WorkspaceServiceImpl
from workspace.create.workspace_create import WorkspaceCreate, RuleCreate
from workspace.upsert.workspace_upsert import WorkspaceUpsert
from workspace.response.workspace_response import WorkspaceResponse, RuleResponse

router = APIRouter()
user_service = UserServiceImpl("config.json")
audit_log_service = AuditLogServiceImpl("config.json")
workspace_service = WorkspaceServiceImpl(user_service, audit_log_service)

@router.post("/{user_id}/add", response_model=WorkspaceResponse)
async def add_workspace(user_id: str, ws_data: WorkspaceCreate, current_user=Depends(get_current_user)):
    try:
        ws = Workspace.create(ws_data.name, ws_data.description)
        added = workspace_service.add_workspace(user_id, ws)
        if not added:
            raise ExpectionHandler(
                message=f"User with ID '{user_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return WorkspaceResponse(**added.to_dict())

    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to add workspace.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.get("/{user_id}/workspaces", response_model=List[WorkspaceResponse])
async def list_workspaces(user_id: str, current_user=Depends(get_current_user)):
    try:
        workspaces = workspace_service.get_workspaces(user_id)
        return [WorkspaceResponse(**ws.to_dict()) for ws in workspaces]
    except Exception as e:
        raise ExpectionHandler(
            message="Error while listing workspaces.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.put("/{user_id}/update/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(user_id: str, workspace_id: str, ws_data: WorkspaceUpsert, current_user=Depends(get_current_user)):
    try:
        updates = ws_data.dict(exclude_unset=True)
        updated = workspace_service.update_workspace(user_id, workspace_id, updates)
        if not updated:
            raise ExpectionHandler(
                message=f"Workspace with ID '{workspace_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return WorkspaceResponse(**updated.to_dict())
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while updating workspace.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.delete("/{user_id}/delete/{workspace_id}")
async def delete_workspace(user_id: str, workspace_id: str, current_user=Depends(get_current_user)):
    try:
        success = workspace_service.remove_workspace(user_id, workspace_id)
        if not success:
            raise ExpectionHandler(
                message=f"Workspace with ID '{workspace_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return {"deleted": True, "message": "Workspace deleted successfully."}
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to delete workspace.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.post("/{user_id}/{workspace_id}/rules", response_model=RuleResponse)
async def add_rule(user_id: str, workspace_id: str, rule_data: RuleCreate, current_user=Depends(get_current_user)):
    try:
        rule = Rule.create(rule_data.name, rule_data.description, rule_data.type, rule_data.params)
        added = workspace_service.add_rule(user_id, workspace_id, rule)
        if not added:
            raise ExpectionHandler(
                message=f"Workspace with ID '{workspace_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return RuleResponse(**added.to_dict())
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to add rule to workspace.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.delete("/{user_id}/{workspace_id}/rules/{rule_id}")
async def delete_rule(user_id: str, workspace_id: str, rule_id: str, current_user=Depends(get_current_user)):
    try:
        success = workspace_service.remove_rule(user_id, workspace_id, rule_id)
        if not success:
            raise ExpectionHandler(
                message=f"Rule with ID '{rule_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return {"deleted": True, "message": f"Rule {rule_id} deleted successfully."}
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Error while deleting rule.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.post("/{user_id}/{workspace_id}/violations")
async def add_violation(user_id: str, workspace_id: str, violation_data: dict, current_user=Depends(get_current_user)):
    try:
        violation = Violation.create(
            user_id=violation_data["user_id"],
            rule_id=violation_data["rule_id"],
            description=violation_data["description"],
            severity=violation_data.get("severity")
        )
        added = workspace_service.add_violation(user_id, workspace_id, violation)
        if not added:
            raise ExpectionHandler(
                message=f"Workspace with ID '{workspace_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return added.to_dict()
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while adding violation.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.get("/{user_id}/{workspace_id}/violations")
async def list_violations(user_id: str, workspace_id: str, current_user=Depends(get_current_user)):
    try:
        violations = workspace_service.get_violations(user_id, workspace_id)
        return [v.to_dict() for v in violations]
    except Exception as e:
        raise ExpectionHandler(
            message="Error while listing violations.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.put("/{user_id}/{workspace_id}/violations/{violation_id}")
async def update_violation(user_id: str, workspace_id: str, violation_id: str, updates: dict, current_user=Depends(get_current_user)):
    try:
        updated = workspace_service.update_violation(user_id, workspace_id, violation_id, updates)
        if not updated:
            raise ExpectionHandler(
                message=f"Violation with ID '{violation_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return updated.to_dict()
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while updating violation.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.delete("/{user_id}/{workspace_id}/violations/{violation_id}")
async def delete_violation(user_id: str, workspace_id: str, violation_id: str, current_user=Depends(get_current_user)):
    try:
        success = workspace_service.remove_violation(user_id, workspace_id, violation_id)
        if not success:
            raise ExpectionHandler(
                message=f"Violation with ID '{violation_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return {"deleted": True, "message": f"Violation {violation_id} deleted successfully."}
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while deleting violation.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )
