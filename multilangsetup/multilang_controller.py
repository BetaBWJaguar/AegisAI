# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict

from multilangsetup.multilang_serviceimpl import MultiLangServiceImpl
from multilangsetup.obsfucationresolver.obsfucation_resolver import ObfuscationResolver
from multilangsetup.schemas.multilang_request import PrepareRequest
from multilangsetup.schemas.multilang_response import PrepareResponse

from error.errortypes import ErrorType
from error.expectionhandler import ExpectionHandler
from permcontrol.permissionscontrol import require_perm
from user.role import Role
from fastapi.responses import JSONResponse


router = APIRouter()
service = MultiLangServiceImpl()


@router.post(
    "/prepare",
    response_model=PrepareResponse,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def prepare_text(data: PrepareRequest):
    try:
        text = data.text
        lang = data.lang
        pipeline = data.pipeline

        if data.apply_obfuscation_resolver:
            try:
                text = ObfuscationResolver.resolve_all(text, lang or "tr")
            except Exception as e:
                print(f"[WARN] ObfuscationResolver failed: {e}")

        if isinstance(pipeline, set):
            pipeline = list(pipeline)
        pipeline_tuple = tuple(pipeline) if pipeline is not None else None

        result = service.prepare(text=text, lang=lang, pipeline=pipeline_tuple)
        return PrepareResponse(**result)

    except ValueError as e:
        raise ExpectionHandler(
            message="Validation failed while preparing text.",
            error_type=ErrorType.VALIDATION_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise ExpectionHandler(
            message="Unexpected error occurred while preparing text.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )



@router.post(
    "/bulk",
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def prepare_bulk(payload: Dict[str, List[str]]):
    try:
        texts = payload.get("texts", [])
        if not texts:
            raise ExpectionHandler(
                message="No texts provided.",
                error_type=ErrorType.VALIDATION_ERROR
            )

        results = []
        default_pipeline = ("normalize", "detect_language", "lang_normalize", "analyze", "linguistics")

        for text in texts:
            try:
                processed = service.prepare(
                    text=text,
                    lang=None,
                    pipeline=default_pipeline
                )
                results.append(processed)
            except Exception as e:
                results.append({"text": text, "error": str(e)})

        return JSONResponse(content={"count": len(results), "results": results})

    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to process bulk texts.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


