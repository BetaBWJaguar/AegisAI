from fastapi import APIRouter, Depends
from typing import Dict, List

from dataset_builder.synonym.synonym_serviceimpl import SynonymServiceImpl
from error.errortypes import ErrorType
from error.expectionhandler import ExpectionHandler
from permcontrol.permissionscontrol import require_perm
from user.role import Role

router = APIRouter()
service = SynonymServiceImpl("config.json")


@router.get(
    "/",
    response_model=Dict[str, List[str]],
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def get_all_synonyms():
    try:
        return service.get_all_synonyms()
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to fetch synonyms.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.get(
    "/{word}",
    response_model=List[str],
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def get_synonym(word: str):
    try:
        synonyms = service.get_synonym(word)
        if synonyms is None:
            raise ExpectionHandler(
                message=f"Synonyms for word '{word}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return synonyms
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to fetch synonym.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.post(
    "/",
    response_model=dict,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def add_synonym(word: str, synonyms: List[str]):
    try:
        if not word:
            raise ExpectionHandler(
                message="Word is required.",
                error_type=ErrorType.VALIDATION_ERROR
            )
        if not synonyms:
            raise ExpectionHandler(
                message="At least one synonym is required.",
                error_type=ErrorType.VALIDATION_ERROR
            )

        success = service.add_synonym(word, synonyms)
        if not success:
            raise ExpectionHandler(
                message="Failed to add synonym.",
                error_type=ErrorType.DATABASE_ERROR
            )

        return {
            "status": "success",
            "message": f"Synonyms for word '{word}' added successfully.",
            "word": word.lower(),
            "synonyms": [s.lower() for s in synonyms]
        }
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to add synonym.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.post(
    "/bulk",
    response_model=dict,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def add_synonyms_bulk(synonym_dict: Dict[str, List[str]]):
    try:
        if not synonym_dict:
            raise ExpectionHandler(
                message="Synonym dictionary is required.",
                error_type=ErrorType.VALIDATION_ERROR
            )

        success = service.add_synonyms_bulk(synonym_dict)
        if not success:
            raise ExpectionHandler(
                message="Failed to add synonyms.",
                error_type=ErrorType.DATABASE_ERROR
            )

        return {
            "status": "success",
            "message": f"Added synonyms for {len(synonym_dict)} words.",
            "count": len(synonym_dict)
        }
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to add synonyms in bulk.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.put(
    "/{word}",
    response_model=dict,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def update_synonym(word: str, synonyms: List[str]):
    try:
        if not word:
            raise ExpectionHandler(
                message="Word is required.",
                error_type=ErrorType.VALIDATION_ERROR
            )
        if not synonyms:
            raise ExpectionHandler(
                message="At least one synonym is required.",
                error_type=ErrorType.VALIDATION_ERROR
            )

        success = service.update_synonym(word, synonyms)
        if not success:
            raise ExpectionHandler(
                message=f"Synonyms for word '{word}' not found.",
                error_type=ErrorType.NOT_FOUND
            )

        return {
            "status": "success",
            "message": f"Synonyms for word '{word}' updated successfully.",
            "word": word.lower(),
            "synonyms": [s.lower() for s in synonyms]
        }
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to update synonym.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.delete(
    "/{word}",
    response_model=dict,
    dependencies=[Depends(require_perm([Role.DEVELOPER, Role.ADMIN]))]
)
async def delete_synonym(word: str):
    try:
        success = service.delete_synonym(word)
        if not success:
            raise ExpectionHandler(
                message=f"Synonyms for word '{word}' not found.",
                error_type=ErrorType.NOT_FOUND
            )

        return {
            "status": "success",
            "message": f"Synonyms for word '{word}' deleted successfully."
        }
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to delete synonym.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.delete(
    "/",
    response_model=dict,
    dependencies=[Depends(require_perm([Role.ADMIN]))]
)
async def clear_all_synonyms():
    try:
        success = service.clear_all_synonyms()
        return {
            "status": "success",
            "message": "All synonyms cleared successfully."
        }
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to clear synonyms.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )
