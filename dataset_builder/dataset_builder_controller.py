from fastapi import APIRouter, HTTPException, Depends
from typing import List

from dataset_builder_serviceimpl import DatasetBuilderServiceImpl
from dataset_builder.datasettype import DatasetType
from permcontrol.permissionscontrol import require_perm
from user.role import Role

router = APIRouter(prefix="/datasets", tags=["Datasets"])
service = DatasetBuilderServiceImpl("config.json")


@router.post("/", response_model=dict, dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))])
async def create_dataset(name: str, description: str, dataset_type: DatasetType):
    ds = service.create_dataset(name, description, dataset_type)
    return ds.to_dict()


@router.get("/", response_model=List[dict], dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))])
async def list_datasets():
    return [d.to_dict() for d in service.list_datasets()]


@router.get("/{dataset_id}", response_model=dict, dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))])
async def get_dataset(dataset_id: str):
    ds = service.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds.to_dict()


@router.post("/{dataset_id}/entries", response_model=dict, dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))])
async def add_entry(dataset_id: str, text: str, label: str,
                    template_id: str = None, values: dict = None):
    entry = service.add_entry(dataset_id, text, label)
    if not entry:
        raise HTTPException(status_code=404, detail="Dataset not found")
    entry.template_id = template_id
    entry.values = values
    return entry.to_dict()


@router.delete("/{dataset_id}/entries/{entry_id}", response_model=dict, dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))])
async def remove_entry(dataset_id: str, entry_id: str):
    ds = service.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    ok = ds.remove_entry(entry_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "success", "message": f"Entry {entry_id} removed"}


@router.delete("/{dataset_id}", response_model=dict, dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))])
async def delete_dataset(dataset_id: str):
    ok = service.delete_dataset(dataset_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"status": "success", "message": "Dataset deleted"}
