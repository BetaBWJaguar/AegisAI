from pydantic import BaseModel
from typing import Dict, List


class DetectResponse(BaseModel):
    raw_text: str
    processed_text: str
    workspace_id: str
    workspace_language: str
    model_name_used: str
    model_path_used: str
    probabilities: Dict[str, float]
    predicted_label: str
    steps_executed: List[str]
