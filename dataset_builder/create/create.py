from pydantic import BaseModel
from dataset_builder.datasettype import DatasetType

class DatasetCreate(BaseModel):
    name: str
    description: str
    dataset_type: DatasetType
