# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from typing import Optional
from huggingface.huggingfacemanager import HuggingFaceManager
from permcontrol.permissionscontrol import require_perm
from user.role import Role
from error.expectionhandler import ExpectionHandler
from error.errortypes import ErrorType

router = APIRouter()
hf = HuggingFaceManager()


@router.post("/load", dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def load_dataset(name: str, subset: Optional[str] = None, split: str = "train"):
    try:
        hf.load(name, subset, split)
        return {"success": True, "datasets": hf.list()}
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to load dataset.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/list", dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def list_datasets():
    try:
        return {"success": True, "datasets": hf.list()}
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to list datasets.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/preview", dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def preview_dataset(key: str, n: int = 5):
    try:
        result = hf.preview(key, n)
        if not result:
            raise ExpectionHandler(
                message=f"Dataset '{key}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return {"success": True, "preview": result}
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to preview dataset.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/save", dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def save_dataset(key: str, output_dir: str = "saved_datasets"):
    try:
        hf.save(key, output_dir)
        return {"success": True, "saved_to": output_dir}
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to save dataset.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
