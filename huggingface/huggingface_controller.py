# -*- coding: utf-8 -*-
from fastapi import APIRouter
from typing import Optional
from huggingface.huggingfacemanager import HuggingFaceManager

router = APIRouter()

hf = HuggingFaceManager()


@router.post("/dataset/add")
def add_dataset(name: str, subset: Optional[str] = None, split: str = "train"):
    hf.add_dataset(name, subset, split)
    return {"success": True, "datasets": hf.list_datasets()}


@router.get("/dataset/list")
def list_datasets():
    return hf.list_datasets()


@router.get("/dataset/preview")
def preview(key: str, n: int = 5):
    result = hf.preview(key, n)
    return result or {"error": "Dataset not found"}


@router.post("/dataset/save")
def save_dataset(key: str, output_dir: str = "saved_datasets"):
    hf.save_dataset(key, output_dir)
    return {"success": True, "saved_to": output_dir}
