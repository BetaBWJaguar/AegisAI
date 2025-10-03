from fastapi import APIRouter, HTTPException, Depends
from typing import List

from template.create.create import TemplateCreate
from template.response.response import TemplateResponse
from template.templateserviceimpl import TemplateServiceImpl
from template.upsert.upsert import TemplateUpsert
from auth.permissions import require_perm
from auth.roles import Role

router = APIRouter(prefix="/templates", tags=["templates"])

service = TemplateServiceImpl()

@router.post("/", response_model=TemplateResponse,
             dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def create_template(data: TemplateCreate):
    tpl = service.create_template(data)
    return TemplateResponse(**tpl.to_dict())

@router.get("/{template_id}", response_model=TemplateResponse,
            dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def get_template(template_id: str):
    tpl = service.get_template(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse(**tpl.to_dict())

@router.get("/", response_model=List[TemplateResponse],
            dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def list_templates():
    return [TemplateResponse(**tpl.to_dict()) for tpl in service.list_templates()]

@router.put("/{template_id}", response_model=TemplateResponse,
            dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def update_template(template_id: str, data: TemplateUpsert):
    tpl = service.update_template(template_id, data)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse(**tpl.to_dict())

@router.delete("/{template_id}",
               dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def delete_template(template_id: str):
    deleted = service.delete_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"success": True}
