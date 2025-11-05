# -*- coding: utf-8 -*-
from fastapi import APIRouter
from typing import Optional
from huggingface.huggingfacemanager import HuggingFaceManager
from corpusmanager import CorpusManager

router = APIRouter()

hf = HuggingFaceManager()
corpus = CorpusManager(hf_manager=hf)


@router.post("/build")
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


@router.get("/list")
def list_corpora():
    return corpus.list_corpora()


@router.get("/preview")
def preview(output_name: str, n: int = 5):
    return corpus.preview(output_name, n)


@router.get("/metadata")
def metadata(output_name: str):
    return corpus.get_metadata(output_name)


@router.get("/analyze")
def analyze(output_name: str):
    return corpus.analyze(output_name)


@router.delete("/delete")
def delete(output_name: str):
    return {"deleted": corpus.delete_corpus(output_name)}
