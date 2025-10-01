from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid
from typing import Optional, List, Dict

from dataset_builder.datasettype import DatasetType


@dataclass
class DatasetEntry:
    text: str
    label: str

    def to_dict(self) -> dict:
        return {"text": self.text, "label": self.label}

@dataclass
class DatasetBuilder:
    id: uuid.UUID
    name: str
    description: str
    dataset_type: DatasetType
    created_at: datetime
    updated_at: datetime
    entries: List[DatasetEntry] = field(default_factory=list)
    _id: Optional[str] = None

    @staticmethod
    def create(name: str, description: str, dataset_type: DatasetType) -> "DatasetBuilder":
        now = datetime.utcnow()
        return DatasetBuilder(
            id=uuid.uuid4(),
            name=name,
            description=description,
            dataset_type=dataset_type,
            created_at=now,
            updated_at=now,
            entries=[]
        )

    def add_entry(self, text: str, label: str):
        self.entries.append(DatasetEntry(text=text, label=label))
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)
        data["dataset_type"] = self.dataset_type.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["entries"] = [e.to_dict() for e in self.entries]
        return data
