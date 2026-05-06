from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List, Optional

from customrules.create.create import RuleCreate
from customrules.customrule_service_impl import CustomRuleServiceImpl
from customrules.response.response import RuleResponse
from customrules.upsert.upsert import RuleUpsert
from error.errortypes import ErrorType
from error.expectionhandler import ExpectionHandler
from permcontrol.permissionscontrol import require_perm
from user.role import Role

router = APIRouter()
service = CustomRuleServiceImpl(config_file="config.json")



class TestPatternRequest(BaseModel):
    pattern: str
    rule_type: str
    test_text: str
    case_sensitive: bool = False


class BulkToggleRequest(BaseModel):
    rule_ids: List[str]
    enabled: bool



@router.post(
    "/",
    response_model=RuleResponse,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))],
)
def create_rule(data: RuleCreate):
    try:
        rule = service.create_rule(data)
        return RuleResponse(**rule.to_dict())
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to create custom rule.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e),
        )


@router.get(
    "/",
    response_model=List[RuleResponse],
)
def list_rules(
    workspace_id: Optional[str] = Query(default=None),
    rule_type: Optional[str] = Query(default=None),
    enabled_only: bool = Query(default=False),
):
    try:
        rules = service.list_rules(
            workspace_id=workspace_id,
            rule_type=rule_type,
            enabled_only=enabled_only,
        )
        return [RuleResponse(**rule.to_dict()) for rule in rules]
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to list custom rules.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e),
        )


@router.get(
    "/search",
    response_model=List[RuleResponse],
)
def search_rules(
    query: str = Query(..., min_length=1),
    workspace_id: Optional[str] = Query(default=None),
):
    try:
        rules = service.search_rules(query=query, workspace_id=workspace_id)
        return [RuleResponse(**rule.to_dict()) for rule in rules]
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to search custom rules.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e),
        )


@router.get(
    "/count",
)
def count_rules(
    workspace_id: Optional[str] = Query(default=None),
    rule_type: Optional[str] = Query(default=None),
    enabled_only: bool = Query(default=False),
):
    try:
        count = service.count_rules(
            workspace_id=workspace_id,
            rule_type=rule_type,
            enabled_only=enabled_only,
        )
        return {"count": count}
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to count custom rules.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e),
        )


@router.get(
    "/by-tag/{tag}",
    response_model=List[RuleResponse],
)
def get_rules_by_tag(
    tag: str,
    workspace_id: Optional[str] = Query(default=None),
):
    try:
        rules = service.get_rules_by_tag(tag=tag, workspace_id=workspace_id)
        return [RuleResponse(**rule.to_dict()) for rule in rules]
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to retrieve rules by tag.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e),
        )


@router.post(
    "/test-pattern",
)
def test_pattern(data: TestPatternRequest):
    try:
        result = service.test_pattern(
            pattern=data.pattern,
            rule_type=data.rule_type,
            test_text=data.test_text,
            case_sensitive=data.case_sensitive,
        )
        return result
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to test pattern.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e),
        )


@router.get(
    "/{rule_id}",
    response_model=RuleResponse,
)
def get_rule(rule_id: str):
    try:
        rule = service.get_rule(rule_id)
        if not rule:
            raise ExpectionHandler(
                message="Rule not found.",
                error_type=ErrorType.NOT_FOUND,
                detail=f"Custom rule with ID {rule_id} not found.",
            )
        return RuleResponse(**rule.to_dict())
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to retrieve custom rule.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e),
        )


@router.put(
    "/{rule_id}",
    response_model=RuleResponse,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))],
)
def update_rule(rule_id: str, data: RuleUpsert):
    try:
        rule = service.update_rule(rule_id, data)
        if not rule:
            raise ExpectionHandler(
                message="Rule not found.",
                error_type=ErrorType.NOT_FOUND,
                detail=f"Custom rule with ID {rule_id} not found for update.",
            )
        return RuleResponse(**rule.to_dict())
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to update custom rule.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e),
        )


@router.patch(
    "/{rule_id}/toggle",
    response_model=RuleResponse,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))],
)
def toggle_rule(rule_id: str):
    try:
        rule = service.toggle_rule(rule_id)
        if not rule:
            raise ExpectionHandler(
                message="Rule not found.",
                error_type=ErrorType.NOT_FOUND,
                detail=f"Custom rule with ID {rule_id} not found for toggle.",
            )
        return RuleResponse(**rule.to_dict())
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to toggle custom rule.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e),
        )


@router.post(
    "/{rule_id}/duplicate",
    response_model=RuleResponse,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))],
)
def duplicate_rule(rule_id: str):
    try:
        rule = service.duplicate_rule(rule_id)
        if not rule:
            raise ExpectionHandler(
                message="Rule not found.",
                error_type=ErrorType.NOT_FOUND,
                detail=f"Custom rule with ID {rule_id} not found for duplication.",
            )
        return RuleResponse(**rule.to_dict())
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to duplicate custom rule.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e),
        )


@router.delete(
    "/{rule_id}",
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))],
)
def delete_rule(rule_id: str):
    try:
        deleted = service.delete_rule(rule_id)
        if not deleted:
            raise ExpectionHandler(
                message="Rule not found.",
                error_type=ErrorType.NOT_FOUND,
                detail=f"Custom rule with ID {rule_id} not found for deletion.",
            )
        return {"success": True, "message": f"Rule {rule_id} deleted successfully."}
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to delete custom rule.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e),
        )


@router.patch(
    "/bulk/toggle",
    response_model=List[RuleResponse],
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))],
)
def bulk_toggle(data: BulkToggleRequest):
    try:
        rules = service.bulk_toggle(rule_ids=data.rule_ids, enabled=data.enabled)
        return [RuleResponse(**rule.to_dict()) for rule in rules]
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to bulk toggle custom rules.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e),
        )


@router.delete(
    "/workspace/{workspace_id}",
    dependencies=[Depends(require_perm([Role.ADMIN]))],
)
def delete_rules_by_workspace(workspace_id: str):
    try:
        deleted_count = service.delete_rules_by_workspace(workspace_id)
        return {
            "success": True,
            "message": f"{deleted_count} rules deleted for workspace {workspace_id}.",
        }
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to delete custom rules by workspace.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e),
        )
