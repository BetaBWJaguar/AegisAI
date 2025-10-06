from fastapi import APIRouter, HTTPException, Depends
from typing import List

from error.errortypes import ErrorType
from error.expectionhandler import ExpectionHandler
from template.create.create import TemplateCreate
from template.response.response import TemplateResponse
from template.templateserviceimpl import TemplateServiceImpl
from template.upsert.upsert import TemplateUpsert
from permcontrol.permissionscontrol import require_perm
from user.role import Role

router = APIRouter()

service = TemplateServiceImpl()

@router.post(
    "/",
    response_model=TemplateResponse,
    dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))]
)
def create_template(data: TemplateCreate):
    try:
        tpl = service.create_template(data)
        return TemplateResponse(**tpl.to_dict())
    except ValueError as e:
        raise ExpectionHandler(
            message="Validation failed while creating template.",
            error_type=ErrorType.VALIDATION_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise ExpectionHandler(
            message="An unexpected error occurred while creating template.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))]
)
def get_template(template_id: str):
    try:
        tpl = service.get_template(template_id)
        if not tpl:
            raise ExpectionHandler(
                message=f"Template with ID '{template_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return TemplateResponse(**tpl.to_dict())
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="An error occurred while fetching template.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=List[TemplateResponse],
    dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))]
)
def list_templates():
    try:
        templates = service.list_templates()
        return [TemplateResponse(**tpl.to_dict()) for tpl in templates]
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to list templates.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.put(
    "/{template_id}",
    response_model=TemplateResponse,
    dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))]
)
def update_template(template_id: str, data: TemplateUpsert):
    try:
        tpl = service.update_template(template_id, data)
        if not tpl:
            raise ExpectionHandler(
                message=f"Template with ID '{template_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return TemplateResponse(**tpl.to_dict())
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Error while updating template.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.delete(
    "/{template_id}",
    dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))]
)
def delete_template(template_id: str):
    try:
        deleted = service.delete_template(template_id)
        if not deleted:
            raise ExpectionHandler(
                message=f"Template with ID '{template_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return {"success": True, "message": "Template deleted successfully."}
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to delete template.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )
