# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from typing import Optional
from huggingface.huggingfacemanager import HuggingFaceManager
from corpusmanagement.corpusmanager import CorpusManager
from permcontrol.permissionscontrol import require_perm
from user.role import Role

router = APIRouter()

hf = HuggingFaceManager()
corpus = CorpusManager(hf_manager=hf)


@router.post("/build", dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def build(
        dataset_key: str,
        output_name: str,
        text_field: str = "text",
        limit: Optional[int] = None
):
    result = corpus.build_corpus(
        dataset_key=dataset_key,
        output_name=output_name,
        text_field=text_field,
        limit=limit,
        filters=[lambda x: len(x) > 3],
        transformers=[lambda x: x.lower()]
    )
    return result


@router.get("/list", dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def list_corpora():
    return corpus.list_corpora()


@router.get("/preview", dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def preview(output_name: str, n: int = 5):
    return corpus.preview(output_name, n)


@router.get("/metadata", dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def metadata(output_name: str):
    return corpus.get_metadata(output_name)


@router.get("/analyze", dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def analyze(output_name: str):
    return corpus.analyze(output_name)


@router.delete("/delete", dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))])
def delete(output_name: str):
    return {"deleted": corpus.delete_corpus(output_name)}
