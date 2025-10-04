from pydantic import BaseModel
from typing import Optional
from dataset_builder.datasettype import DatasetType

class DatasetUpsert(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dataset_type: Optional[DatasetType] = None
