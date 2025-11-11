# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from pydantic import BaseModel

from trainer.base_trainer.base_trainer import BaseTrainer
from user.role import Role
from permcontrol.permissionscontrol import require_perm
from error.expectionhandler import ExpectionHandler
from error.errortypes import ErrorType

router = APIRouter()
trainer = BaseTrainer()


class TrainRequest(BaseModel):
    corpus_files: List[str]
    output_dir: str


@router.post(
    "/train-model",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))]
)
async def train_language_model(request: TrainRequest):
    try:
        result = trainer.train(request.corpus_files, request.output_dir)
        return {
            "success": True,
            "task": "base_language_model_training",
            **result
        }
    except FileNotFoundError as e:
        raise ExpectionHandler(
            message=f"File not found: {str(e)}",
            error_type=ErrorType.NOT_FOUND,
            detail="One or more corpus files required for training could not be found.",
            context={"corpus_files": request.corpus_files}
        )
    except ValueError as e:
        raise ExpectionHandler(
            message=str(e),
            error_type=ErrorType.VALIDATION_ERROR,
            detail="Invalid input values were provided for training.",
            context={"output_dir": request.output_dir}
        )
    except Exception as e:
        raise ExpectionHandler(
            message="An unexpected error occurred during base model training.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e),
            context={"output_dir": request.output_dir}
        )