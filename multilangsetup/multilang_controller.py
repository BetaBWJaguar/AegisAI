# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict

from multilangsetup.multilang_serviceimpl import MultiLangServiceImpl
from multilangsetup.multilang_step import Step
from multilangsetup.obsfucationresolver.obsfucation_resolver import ObfuscationResolver
from multilangsetup.schemas.multilang_request import PrepareRequest, BulkRequest
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
        original_text = data.text
        lang = data.lang
        pipeline = data.pipeline

        text = original_text
        if data.apply_obfuscation_resolver:
            try:
                text = ObfuscationResolver.resolve_all(text, lang or "tr")
            except Exception as e:
                print(f"[WARN] ObfuscationResolver failed: {e}")

        if pipeline:
            pipeline = [Step(p) for p in pipeline]

        result = service.prepare(text=text, lang=lang, pipeline=pipeline)
        result["raw_text"] = original_text

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
async def prepare_bulk(payload: BulkRequest):
    try:
        texts = payload.texts
        apply_resolver = payload.apply_obfuscation_resolver
        lang = payload.lang

        if not texts:
            raise ExpectionHandler(
                message="No texts provided.",
                error_type=ErrorType.VALIDATION_ERROR
            )

        default_pipeline = [
            Step.NORMALIZE,
            Step.DETECT_LANGUAGE,
            Step.LANG_NORMALIZE,
            Step.ANALYZE,
            Step.KEYWORDS,
            Step.LINGUISTICS
        ]

        results = []

        for original_text in texts:
            text = original_text

            try:
                if apply_resolver:
                    try:
                        text = ObfuscationResolver.resolve_all(text, lang or "tr")
                    except Exception as e:
                        print(f"[WARN] ObfuscationResolver failed for '{original_text[:30]}...': {e}")

                processed = service.prepare(
                    text=text,
                    lang=lang,
                    pipeline=default_pipeline
                )

                processed["raw_text"] = original_text
                results.append(processed)

            except Exception as e:
                results.append({
                    "raw_text": original_text,
                    "text": original_text,
                    "error": str(e)
                })

        return JSONResponse(content={"count": len(results), "results": results})

    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to process bulk texts.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


