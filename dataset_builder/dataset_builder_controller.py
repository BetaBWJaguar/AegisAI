from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from dataset_builder.dataset_builder_serviceimpl import DatasetBuilderServiceImpl
from dataset_builder.entrytype import EntryType
from dataset_builder.create.create import DatasetCreate
from dataset_builder.response.response import DatasetResponse
from dataset_builder.upsert.upsert import DatasetUpsert
from permcontrol.permissionscontrol import require_perm
from user.role import Role

router = APIRouter()
service = DatasetBuilderServiceImpl("config.json")


@router.post("/", response_model=DatasetResponse,
             dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))])
async def create_dataset(data: DatasetCreate):
    ds = service.create_dataset(data.name, data.description, data.dataset_type)
    return DatasetResponse(**ds.to_dict())


@router.get("/", response_model=List[DatasetResponse],
            dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))])
async def list_datasets():
    return [DatasetResponse(**d.to_dict()) for d in service.list_datasets()]


@router.get("/{dataset_id}", response_model=DatasetResponse,
            dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))])
async def get_dataset(dataset_id: str):
    ds = service.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetResponse(**ds.to_dict())


@router.post("/{dataset_id}/entries",
             response_model=dict,
             dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))])
async def add_entry(
        dataset_id: str,
        text: Optional[str] = None,
        label: Optional[str] = None,
        entry_type: EntryType = EntryType.MANUAL,
        template_id: Optional[str] = None,
        values: Optional[dict] = None
):
    entry = service.add_entry(
        dataset_id=dataset_id,
        text=text,
        label=label,
        entry_type=entry_type,
        template_id=template_id,
        values=values
    )

    if not entry:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if isinstance(entry, list):
        return {
            "status": "success",
            "count": len(entry),
            "entries": [e.to_dict() for e in entry]
        }

    return entry.to_dict()


@router.delete("/{dataset_id}/entries/{entry_id}",
               response_model=dict,
               dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))])
async def remove_entry(dataset_id: str, entry_id: str):
    ds = service.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    ok = ds.remove_entry(entry_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Entry not found")

    service.collection.update_one(
        {"id": dataset_id},
        {"$set": {
            "entries": [e.to_dict() for e in ds.entries],
            "updated_at": ds.updated_at.isoformat()
        }}
    )

    return {"status": "success", "message": f"Entry {entry_id} removed"}


@router.delete("/{dataset_id}", response_model=dict,
               dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))])
async def delete_dataset(dataset_id: str):
    ok = service.delete_dataset(dataset_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"status": "success", "message": "Dataset deleted"}
