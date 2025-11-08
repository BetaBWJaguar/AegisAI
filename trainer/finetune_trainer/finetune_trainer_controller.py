# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from typing import Dict, Any

from trainer.finetune_trainer.finetune_trainer import FineTuneTrainer
from user.role import Role
from permcontrol.permissionscontrol import require_perm
from error.expectionhandler import ExpectionHandler
from error.errortypes import ErrorType

router = APIRouter()
trainer = FineTuneTrainer()

@router.post(
    "/fine-tune",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))]
)
async def fine_tune_model(
        model_path: str,
        dataset_id: str,
        output_dir: str,
        training_args: Dict[str, Any]
):
    try:
        result = trainer.fine_tune(model_path, dataset_id, output_dir, training_args)
        return {
            "success": True,
            "task": "fine_tuning",
            **result
        }

    except FileNotFoundError as e:
        raise ExpectionHandler(
            message=f"Model or file not found: {str(e)}",
            error_type=ErrorType.NOT_FOUND,
            detail="The model path or one of the required files for fine-tuning does not exist.",
            context={"model_path": model_path}
        )

    except ValueError as e:
        raise ExpectionHandler(
            message=str(e),
            error_type=ErrorType.VALIDATION_ERROR,
            detail="Invalid dataset or label information was provided.",
            context={"dataset_id": dataset_id}
        )

    except Exception as e:
        raise ExpectionHandler(
            message="An unexpected error occurred during fine-tuning.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e),
            context={"output_dir": output_dir}
        )
