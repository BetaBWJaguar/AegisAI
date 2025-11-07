# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from typing import Optional
from huggingface.huggingfacemanager import HuggingFaceManager
from permcontrol.permissionscontrol import require_perm
from user.role import Role

router = APIRouter()
hf = HuggingFaceManager()


@router.post("/add", dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def add_dataset(name: str, subset: Optional[str] = None, split: str = "train"):
    hf.add_dataset(name, subset, split)
    return {"success": True, "datasets": hf.list_datasets()}


@router.get("/list", dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def list_datasets():
    return hf.list_datasets()


@router.get("/preview", dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def preview(key: str, n: int = 5):
    result = hf.preview(key, n)
    return result or {"error": "Dataset not found"}


@router.post("/save", dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def save_dataset(key: str, output_dir: str = "saved_datasets"):
    hf.save_dataset(key, output_dir)
    return {"success": True, "saved_to": output_dir}
