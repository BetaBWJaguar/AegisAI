from fastapi import APIRouter, HTTPException, Depends
from typing import List
from auth.authcontroller import get_current_user
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
workspace_service = WorkspaceServiceImpl(user_service)

@router.post("/{user_id}/workspaces", response_model=WorkspaceResponse)
async def add_workspace(user_id: str, ws_data: WorkspaceCreate, current_user=Depends(get_current_user)):
    ws = Workspace.create(ws_data.name, ws_data.description)

    for r in ws_data.rules:
        ws.add_rule(Rule.create(r.name, r.description, r.type, r.params))

    added = workspace_service.add_workspace(user_id, ws)
    if not added:
        raise HTTPException(status_code=404, detail="User not found")
    return WorkspaceResponse(**added.to_dict())

@router.get("/{user_id}/workspaces", response_model=List[WorkspaceResponse])
async def list_workspaces(user_id: str, current_user=Depends(get_current_user)):
    workspaces = workspace_service.get_workspaces(user_id)
    return [WorkspaceResponse(**ws.to_dict()) for ws in workspaces]

@router.put("/{user_id}/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(user_id: str, workspace_id: str, ws_data: WorkspaceUpsert, current_user=Depends(get_current_user)):
    updates = ws_data.dict(exclude_unset=True)
    updated = workspace_service.update_workspace(user_id, workspace_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceResponse(**updated.to_dict())

@router.delete("/{user_id}/workspaces/{workspace_id}")
async def delete_workspace(user_id: str, workspace_id: str, current_user=Depends(get_current_user)):
    success = workspace_service.remove_workspace(user_id, workspace_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"deleted": True}


@router.post("/{user_id}/workspaces/{workspace_id}/rules", response_model=RuleResponse)
async def add_rule(user_id: str, workspace_id: str, rule_data: RuleCreate, current_user=Depends(get_current_user)):
    rule = Rule.create(rule_data.name, rule_data.description, rule_data.type, rule_data.params)
    added = workspace_service.add_rule(user_id, workspace_id, rule)
    if not added:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return RuleResponse(**added.to_dict())

@router.delete("/{user_id}/workspaces/{workspace_id}/rules/{rule_id}")
async def delete_rule(user_id: str, workspace_id: str, rule_id: str, current_user=Depends(get_current_user)):
    success = workspace_service.remove_rule(user_id, workspace_id, rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"deleted": True}

@router.post("/{user_id}/workspaces/{workspace_id}/violations")
async def add_violation(user_id: str, workspace_id: str, violation_data: dict, current_user=Depends(get_current_user)):
    violation = Violation.create(
        user_id=violation_data["user_id"],
        rule_id=violation_data["rule_id"],
        description=violation_data["description"],
        severity=violation_data.get("severity")
    )
    added = workspace_service.add_violation(user_id, workspace_id, violation)
    if not added:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return added.to_dict()

@router.get("/{user_id}/workspaces/{workspace_id}/violations")
async def list_violations(user_id: str, workspace_id: str, current_user=Depends(get_current_user)):
    violations = workspace_service.get_violations(user_id, workspace_id)
    return [v.to_dict() for v in violations]

@router.put("/{user_id}/workspaces/{workspace_id}/violations/{violation_id}")
async def update_violation(user_id: str, workspace_id: str, violation_id: str, updates: dict, current_user=Depends(get_current_user)):
    updated = workspace_service.update_violation(user_id, workspace_id, violation_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Violation not found")
    return updated.to_dict()

@router.delete("/{user_id}/workspaces/{workspace_id}/violations/{violation_id}")
async def delete_violation(user_id: str, workspace_id: str, violation_id: str, current_user=Depends(get_current_user)):
    success = workspace_service.remove_violation(user_id, workspace_id, violation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Violation not found")
    return {"deleted": True}
