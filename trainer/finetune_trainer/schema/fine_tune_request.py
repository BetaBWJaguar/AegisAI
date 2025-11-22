from pydantic import BaseModel
from typing import Dict, Any

class FineTuneRequest(BaseModel):
    model_path: str
    dataset_id: str
    output_dir: str
    training_args: Dict[str, Any]
