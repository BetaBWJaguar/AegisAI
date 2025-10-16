import io
import tempfile

from fastapi import APIRouter, HTTPException, Depends, Response
from typing import List, Optional
from starlette.responses import StreamingResponse, FileResponse

from dataset_builder.dataset_builder_serviceimpl import DatasetBuilderServiceImpl
from dataset_builder.entrytype import EntryType
from dataset_builder.create.create import DatasetCreate
from dataset_builder.response.response import DatasetResponse
from error.errortypes import ErrorType
from error.expectionhandler import ExpectionHandler
from permcontrol.permissionscontrol import require_perm
from user.role import Role

router = APIRouter()
service = DatasetBuilderServiceImpl("config.json")


@router.post(
    "/",
    response_model=DatasetResponse,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def create_dataset(data: DatasetCreate):
    try:
        ds = service.create_dataset(data.name, data.description, data.dataset_type)
        return DatasetResponse(**ds.to_dict())
    except ValueError as e:
        raise ExpectionHandler(
            message="Validation failed while creating dataset.",
            error_type=ErrorType.VALIDATION_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to create dataset.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=List[DatasetResponse],
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def list_datasets():
    try:
        datasets = service.list_datasets()
        return [DatasetResponse(**d.to_dict()) for d in datasets]
    except Exception as e:
        raise ExpectionHandler(
            message="Error while listing datasets.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def get_dataset(dataset_id: str):
    try:
        ds = service.get_dataset(dataset_id)
        if not ds:
            raise ExpectionHandler(
                message=f"Dataset with ID '{dataset_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return DatasetResponse(**ds.to_dict())
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to fetch dataset.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.post(
    "/{dataset_id}/entries",
    response_model=dict,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def add_entry(
        dataset_id: str,
        text: Optional[str] = None,
        label: Optional[str] = None,
        entry_type: EntryType = EntryType.MANUAL,
        template_id: Optional[str] = None,
        values: Optional[dict] = None
):
    try:
        entry = service.add_entry(
            dataset_id=dataset_id,
            text=text,
            label=label,
            entry_type=entry_type,
            template_id=template_id,
            values=values
        )

        if not entry:
            raise ExpectionHandler(
                message=f"Dataset with ID '{dataset_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )

        if isinstance(entry, list):
            return {
                "status": "success",
                "count": len(entry),
                "entries": [e.to_dict() for e in entry]
            }

        return entry.to_dict()

    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to add entry to dataset.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.delete(
    "/{dataset_id}/entries/{entry_id}",
    response_model=dict,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def remove_entry(dataset_id: str, entry_id: str):
    try:
        ds = service.get_dataset(dataset_id)
        if not ds:
            raise ExpectionHandler(
                message=f"Dataset with ID '{dataset_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )

        ok = ds.remove_entry(entry_id)
        if not ok:
            raise ExpectionHandler(
                message=f"Entry with ID '{entry_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )

        service.collection.update_one(
            {"id": dataset_id},
            {"$set": {
                "entries": [e.to_dict() for e in ds.entries],
                "updated_at": ds.updated_at.isoformat()
            }}
        )

        return {
            "status": "success",
            "message": f"Entry {entry_id} removed successfully."
        }

    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to remove entry from dataset.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.delete(
    "/{dataset_id}",
    response_model=dict,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def delete_dataset(dataset_id: str):
    try:
        ok = service.delete_dataset(dataset_id)
        if not ok:
            raise ExpectionHandler(
                message=f"Dataset with ID '{dataset_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return {"status": "success", "message": "Dataset deleted successfully."}
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while deleting dataset.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.get(
    "/{dataset_id}/export/{export_type}",
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def export_dataset(dataset_id: str, export_type: str):
    try:
        data = service.export_format(dataset_id, export_type)
        if not data:
            raise ExpectionHandler(
                message=f"Dataset with ID '{dataset_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )

        media_types = {
            "json": "application/json",
            "csv": "text/csv",
            "txt": "text/plain"
        }

        return Response(
            content=data,
            media_type=media_types.get(export_type.lower(), "application/octet-stream"),
            headers={
                "Content-Disposition": f'attachment; filename="{dataset_id}.{export_type}"'
            }
        )

    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message=f"Failed to export dataset as {export_type}.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )

@router.post(
    "/{dataset_id}/entries/bulk",
    response_model=dict,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def add_entries_bulk(dataset_id: str, entries: List[dict]):
    try:
        added_entries = service.add_entries_bulk(dataset_id, entries)
        if not added_entries:
            raise ExpectionHandler(
                message=f"Dataset with ID '{dataset_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )

        return {
            "status": "success",
            "count": len(added_entries),
            "entries": [e.to_dict() for e in added_entries]
        }

    except ValueError as e:
        raise ExpectionHandler(
            message="Invalid entry data provided.",
            error_type=ErrorType.VALIDATION_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to add entries in bulk.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.get(
    "/{dataset_id}/entries/search",
    response_model=List[dict],
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def search_entries(dataset_id: str, query: Optional[str] = None, label: Optional[str] = None):
    try:
        results = service.search_entries(dataset_id, query=query, label=label)
        return [e.to_dict() for e in results]
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to search entries.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )

@router.post(
    "/merge",
    response_model=DatasetResponse,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def merge_datasets(
        primary_id: str,
        secondary_id: str,
        remove_dupes: bool,
        new_datasets: bool
):
    try:
        merged = service.merge_datasets(primary_id, secondary_id, remove_dupes,new_datasets)
        if not merged:
            raise ExpectionHandler(
                message="One or both datasets could not be found.",
                error_type=ErrorType.NOT_FOUND
            )

        return DatasetResponse(**merged.to_dict())

    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to merge datasets.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


