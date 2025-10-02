from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid
from typing import Optional, List, Dict

from dataset_builder.datasettype import DatasetType
from dataset_builder.entrytype import EntryType


@dataclass
class DatasetEntry:
    id: uuid.UUID
    text: str
    label: str
    entry_type: EntryType
    template_id: Optional[str] = None
    values: Optional[Dict[str, str]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(text: str, label: str, template_id: Optional[str] = None, values: Optional[Dict[str, str]] = None,
               entry_type: EntryType = None) -> "DatasetEntry":
        return DatasetEntry(
            id=uuid.uuid4(),
            text=text,
            label=label,
            template_id=template_id,
            values=values,
            entry_type=entry_type
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "text": self.text,
            "label": self.label,
            "template_id": self.template_id,
            "values": self.values,
            "created_at": self.created_at.isoformat()
        }


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

    def add_entry(self, text: str, label: str,
                  template_id: Optional[str] = None,
                  values: Optional[Dict[str, str]] = None) -> DatasetEntry:
        entry = DatasetEntry.create(text, label, template_id, values)
        self.entries.append(entry)
        self.updated_at = datetime.utcnow()
        return entry

    def remove_entry(self, entry_id: str) -> bool:
        for e in self.entries:
            if str(e.id) == entry_id:
                self.entries.remove(e)
                self.updated_at = datetime.utcnow()
                return True
        return False

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)
        data["dataset_type"] = self.dataset_type.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["entries"] = [e.to_dict() for e in self.entries]
        return data
