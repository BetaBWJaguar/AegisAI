# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from typing import Dict, Any
from trainer.finetune_trainer.finetune_trainer import FineTuneTrainer
from trainer.finetune_trainer.schema.fine_tune_request import FineTuneRequest
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
async def fine_tune_model(req: FineTuneRequest):
    try:
        result = trainer.fine_tune(
            req.model_path,
            req.dataset_id,
            req.output_dir,
            req.training_args,
            req.model_name,
            req.version
        )

        return {
            "success": True,
            "message": "Fine-tuning completed successfully.",
            "task": result.get("task"),
            "model_info": result.get("model_info"),
            "metrics": result.get("metrics"),
            "saved_path": result.get("saved_path"),
            "raw": result
        }

    except FileNotFoundError as e:
        raise ExpectionHandler(
            message=f"Model or file not found: {str(e)}",
            error_type=ErrorType.NOT_FOUND,
            detail="The model path or a required file does not exist.",
            context={"model_path": req.model_path}
        )

    except ValueError as e:
        raise ExpectionHandler(
            message=str(e),
            error_type=ErrorType.VALIDATION_ERROR,
            detail="Invalid dataset or label information was provided.",
            context={"dataset_id": req.dataset_id}
        )

    except Exception as e:
        raise ExpectionHandler(
            message="An unexpected error occurred during fine-tuning.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e),
            context={"output_dir": req.output_dir}
        )
