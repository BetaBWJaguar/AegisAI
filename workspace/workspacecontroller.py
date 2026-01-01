from datetime import datetime
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
from workspace.response.workspace_response import (
    WorkspaceResponse,
    RuleResponse,
    DoxxingSettingsResponse,
    DoxxingPIIConfigResponse,
    DoxxingContextConfigResponse
)

router = APIRouter()
user_service = UserServiceImpl("config.json")
audit_log_service = AuditLogServiceImpl("config.json")
workspace_service = WorkspaceServiceImpl(user_service, audit_log_service)

@router.post("/{user_id}/add", response_model=WorkspaceResponse)
async def add_workspace(user_id: str, ws_data: WorkspaceCreate, current_user=Depends(get_current_user)):
    try:
        ws = Workspace.create(
            name=ws_data.name,
            description=ws_data.description,
            model_name=ws_data.model_name,
            model_version=ws_data.model_version
        )
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
        required_fields = ["description", "severity", "metadata"]
        missing_fields = [f for f in required_fields if f not in violation_data or not violation_data[f]]
        if missing_fields:
            raise ExpectionHandler(
                message=f"Missing required field(s): {', '.join(missing_fields)}",
                error_type=ErrorType.VALIDATION_ERROR
            )

        violation = Violation.create(
            description=violation_data["description"],
            severity=violation_data["severity"],
            metadata=violation_data["metadata"]
        )

        added = workspace_service.add_violation(user_id, workspace_id, violation)
        if not added:
            raise ExpectionHandler(
                message=f"Workspace with ID '{workspace_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )

        return {
            "success": True,
            "message": "Violation added successfully.",
            "data": added.to_dict()
        }

    except ExpectionHandler:
        raise

    except ValueError as e:
        raise ExpectionHandler(
            message=str(e),
            error_type=ErrorType.VALIDATION_ERROR
        )

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

@router.get(
    "/{user_id}/{workspace_id}/doxxing-settings",
    response_model=DoxxingSettingsResponse
)
async def get_doxxing_settings(
        user_id: str,
        workspace_id: str,
        current_user=Depends(get_current_user)
):
    try:
        settings = workspace_service.get_doxxing_settings(user_id, workspace_id)
        if not settings:
            raise ExpectionHandler(
                message=f"Workspace with ID '{workspace_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return settings.to_dict()
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Error while retrieving doxxing settings.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )



@router.put(
    "/{user_id}/{workspace_id}/doxxing-settings",
    response_model=DoxxingSettingsResponse
)
async def update_doxxing_settings(
        user_id: str,
        workspace_id: str,
        settings: dict,
        current_user=Depends(get_current_user)
):
    try:
        updated = workspace_service.update_doxxing_settings(
            user_id, workspace_id, settings
        )
        if not updated:
            raise ExpectionHandler(
                message=f"Workspace with ID '{workspace_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return updated.to_dict()
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while updating doxxing settings.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )



@router.post("/{user_id}/{workspace_id}/doxxing-settings/toggle")
async def toggle_doxxing_detection(
        user_id: str,
        workspace_id: str,
        enabled: bool = True,
        current_user=Depends(get_current_user)
):
    try:
        settings = workspace_service.get_doxxing_settings(user_id, workspace_id)
        if not settings:
            raise ExpectionHandler(
                message=f"Workspace with ID '{workspace_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )

        settings.enabled = enabled
        workspace_service.update_doxxing_settings(
            user_id,
            workspace_id,
            settings.to_dict()
        )

        return {
            "enabled": enabled,
            "message": f"Doxxing detection {'enabled' if enabled else 'disabled'} successfully."
        }
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while toggling doxxing detection.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )



@router.post(
    "/{user_id}/{workspace_id}/doxxing-settings/pii-config",
    response_model=DoxxingPIIConfigResponse
)
async def update_pii_config(
        user_id: str,
        workspace_id: str,
        pii_type: str,
        enabled: bool = None,
        weight: float = None,
        current_user=Depends(get_current_user)
):
    try:
        config = workspace_service.update_pii_config(
            user_id, workspace_id, pii_type, enabled, weight
        )
        if not config:
            raise ExpectionHandler(
                message=f"Workspace with ID '{workspace_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )

        return config.to_dict()
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while updating PII config.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.post(
    "/{user_id}/{workspace_id}/doxxing-settings/context-config",
    response_model=DoxxingContextConfigResponse
)
async def update_context_config(
        user_id: str,
        workspace_id: str,
        context_type: str,
        enabled: bool = None,
        weight: float = None,
        current_user=Depends(get_current_user)
):
    try:
        config = workspace_service.update_context_config(
            user_id, workspace_id, context_type, enabled, weight
        )
        if not config:
            raise ExpectionHandler(
                message=f"Workspace with ID '{workspace_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )

        return config.to_dict()
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while updating context config.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.post("/{user_id}/{workspace_id}/doxxing-settings/risk-action")
async def set_risk_action(
        user_id: str,
        workspace_id: str,
        risk_tier: str,
        action: str,
        current_user=Depends(get_current_user)
):
    try:
        success = workspace_service.set_risk_action(
            user_id, workspace_id, risk_tier, action
        )
        if not success:
            raise ExpectionHandler(
                message=f"Workspace with ID '{workspace_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )

        return {
            "risk_tier": risk_tier.upper(),
            "action": action.upper(),
            "message": f"Action for {risk_tier.upper()} risk set to {action.upper()}."
        }
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while setting risk action.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )
