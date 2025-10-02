import uuid
from typing import List, Optional
from datetime import datetime
from pymongo import MongoClient
from dataset_builder.dataset_builder import DatasetBuilder, DatasetEntry, DatasetType
from dataset_builder_service import DatasetBuilderService
from config_loader import ConfigLoader


class DatasetBuilderServiceImpl(DatasetBuilderService):
    def __init__(self, config_file: str = "config.json"):
        cfg = ConfigLoader(config_file).get_database_config()
        uri = f"mongodb://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['authSource']}"

        self.client = MongoClient(uri)
        self.db = self.client[cfg["name"]]
        self.collection = self.db["datasets"]


    def create_dataset(self, name: str, description: str, dataset_type: DatasetType) -> DatasetBuilder:
        ds = DatasetBuilder.create(name, description, dataset_type)
        doc = ds.to_dict()
        result = self.collection.insert_one(doc)
        ds._id = str(result.inserted_id)
        return ds


    def add_entry(self, dataset_id: str, text: str, label: str,
                  template_id: Optional[str] = None,
                  values: Optional[dict] = None) -> Optional[DatasetEntry]:
        entry = DatasetEntry.create(text, label, template_id, values)
        update_result = self.collection.update_one(
            {"id": dataset_id},
            {"$push": {"entries": entry.to_dict()},
             "$set": {"updated_at": datetime.utcnow().isoformat()}}
        )
        if update_result.matched_count == 0:
            return None
        return entry


    def remove_entry(self, dataset_id: str, entry_id: str) -> bool:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return False
        ok = dataset.remove_entry(entry_id)
        if not ok:
            return False
        self.collection.update_one(
            {"id": dataset_id},
            {"$set": {
                "entries": [e.to_dict() for e in dataset.entries],
                "updated_at": datetime.utcnow().isoformat()
            }}
        )
        return True


    def get_dataset(self, dataset_id: str) -> Optional[DatasetBuilder]:
        doc = self.collection.find_one({"id": dataset_id})
        if not doc:
            return None
        return DatasetBuilder(
            id=uuid.UUID(doc["id"]),
            name=doc["name"],
            description=doc["description"],
            dataset_type=DatasetType(doc["dataset_type"]),
            created_at=datetime.fromisoformat(doc["created_at"]),
            updated_at=datetime.fromisoformat(doc["updated_at"]),
            entries=[
                DatasetEntry(
                    id=uuid.UUID(e["id"]),
                    text=e["text"],
                    label=e["label"],
                    template_id=e.get("template_id"),
                    values=e.get("values"),
                    created_at=datetime.fromisoformat(e["created_at"]) if e.get("created_at") else datetime.utcnow()
                ) for e in doc.get("entries", [])
            ],
            _id=str(doc["_id"])
        )

    def list_datasets(self) -> List[DatasetBuilder]:
        datasets = []
        for doc in self.collection.find():
            datasets.append(
                DatasetBuilder(
                    id=uuid.UUID(doc["id"]),
                    name=doc["name"],
                    description=doc["description"],
                    dataset_type=DatasetType(doc["dataset_type"]),
                    created_at=datetime.fromisoformat(doc["created_at"]),
                    updated_at=datetime.fromisoformat(doc["updated_at"]),
                    entries=[
                        DatasetEntry(
                            id=uuid.UUID(e["id"]),
                            text=e["text"],
                            label=e["label"],
                            template_id=e.get("template_id"),
                            values=e.get("values"),
                            created_at=datetime.fromisoformat(e["created_at"]) if e.get("created_at") else datetime.utcnow()
                        ) for e in doc.get("entries", [])
                    ],
                    _id=str(doc["_id"])
                )
            )
        return datasets

    def delete_dataset(self, dataset_id: str) -> bool:
        result = self.collection.delete_one({"id": dataset_id})
        return result.deleted_count > 0
