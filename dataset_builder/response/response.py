from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from dataset_builder.datasettype import DatasetType

class DatasetResponse(BaseModel):
    id: str
    name: str
    description: str
    dataset_type: DatasetType
    entries: List[dict] = []
    created_at: datetime
    updated_at: datetime
    _id: Optional[str] = None
