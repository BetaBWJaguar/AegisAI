import io
import csv
import json
import uuid
from typing import List, Optional
from datetime import datetime
from pymongo import MongoClient
from dataset_builder.dataset_builder import DatasetBuilder, DatasetEntry, DatasetType
from dataset_builder.dataset_builder_service import DatasetBuilderService
from dataset_builder.entrytype import EntryType
from config_loader import ConfigLoader
from template.templateserviceimpl import TemplateServiceImpl
from template.utils.templategenerator import TemplateGenerator


class DatasetBuilderServiceImpl(DatasetBuilderService):
    def __init__(self, config_file: str = "config.json"):
        cfg = ConfigLoader(config_file).get_database_config()
        uri = f"mongodb://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['authSource']}"

        self.client = MongoClient(uri)
        self.db = self.client[cfg["name"]]
        self.collection = self.db["datasets"]
        self.template_service = TemplateServiceImpl()
        self.temp_new_dataset_info = None


    def create_dataset(self, name: str, description: str, dataset_type: DatasetType) -> DatasetBuilder:
        ds = DatasetBuilder.create(name, description, dataset_type)
        doc = ds.to_dict()
        result = self.collection.insert_one(doc)
        ds._id = str(result.inserted_id)
        return ds


    def add_entry(self, dataset_id: str, text: Optional[str], label: str,
                  entry_type: EntryType = EntryType.MANUAL,
                  template_id: Optional[str] = None,
                  values: Optional[dict] = None):

        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return None

        if entry_type == EntryType.TEMPLATE:
            if not template_id:
                raise ValueError("template_id is required for TEMPLATE entry type")

            tpl = self.template_service.get_template(template_id)
            if not tpl:
                return None

            dataset_values = {}
            for e in dataset.entries:
                if e.values:
                    for k, v in e.values.items():
                        dataset_values.setdefault(k, set()).add(v)
            dataset_values = {k: list(v) for k, v in dataset_values.items()}

            generator = TemplateGenerator(tpl.pattern)
            input_values = values.get("values") if values and "values" in values else values

            variations = generator.generate_from_dataset_values(input_values or dataset_values)


            added_entries = []
            for var in variations:
                entry = DatasetEntry.create(
                    text=var["text"],
                    label=label,
                    entry_type=EntryType.TEMPLATE,
                    template_id=template_id,
                    values=var["values"]
                )
                self.collection.update_one(
                    {"id": dataset_id},
                    {"$push": {"entries": entry.to_dict()},
                     "$set": {"updated_at": datetime.utcnow().isoformat()}}
                )
                added_entries.append(entry)

            return added_entries

        if not text and values and "text" in values:
            text = values["text"]

        entry = DatasetEntry.create(
            text=text,
            label=label,
            entry_type=EntryType.MANUAL,
            template_id=None,
            values={}
        )

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
                    entry_type=e.get("entry_type"),
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


    def export_format(self, dataset_id: str, export_type: str) -> Optional[bytes]:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return None

        export_type = export_type.lower().strip()
        buffer = io.BytesIO()

        if export_type == "json":
            data = json.dumps(dataset.to_dict(), ensure_ascii=False, indent=4)
            buffer.write(data.encode("utf-8"))

        elif export_type == "csv":
            text_stream = io.StringIO()
            writer = csv.writer(text_stream)
            writer.writerow(["id", "text", "label"])
            for e in dataset.entries:
                writer.writerow([e.id, e.text, e.label])
            buffer.write(text_stream.getvalue().encode("utf-8"))

        elif export_type == "txt":
            content = "\n".join([f"[{e.label}] {e.text}" for e in dataset.entries])
            buffer.write(content.encode("utf-8"))

        else:
            raise ValueError("Unsupported export type. Use 'json', 'csv', or 'txt'.")

        buffer.seek(0)
        return buffer.read()

    def add_entries_bulk(self, dataset_id: str, entries: List[dict]) -> List[DatasetEntry]:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return []

        added_entries = []
        now = datetime.utcnow()

        for entry_data in entries:
            text = entry_data.get("text")
            label = entry_data.get("label")
            entry_type = entry_data.get("entry_type")
            template_id = entry_data.get("template_id")
            values = entry_data.get("values")

            if not text or not label or not entry_type:
                raise ValueError("Each entry must include 'text', 'label', and 'entry_type' fields.")

            entry = DatasetEntry.create(
                text=text,
                label=label,
                entry_type=EntryType(entry_type),
                template_id=template_id,
                values=values
            )
            added_entries.append(entry)

        self.collection.update_one(
            {"id": dataset_id},
            {
                "$push": {"entries": {"$each": [e.to_dict() for e in added_entries]}},
                "$set": {"updated_at": now.isoformat()}
            }
        )
        return added_entries


    def search_entries(self, dataset_id: str, query: Optional[str] = None,
                       label: Optional[str] = None) -> List[DatasetEntry]:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return []

        results = []
        for entry in dataset.entries:
            if query and query.lower() not in entry.text.lower():
                continue
            if label and entry.label.lower() != label.lower():
                continue
            results.append(entry)
        return results


    def merge_datasets(
            self,
            primary_id: str,
            secondary_id: str,
            remove_dupes: bool,
            new_dataset: bool
    ) -> Optional[DatasetBuilder]:
        primary = self.get_dataset(primary_id)
        secondary = self.get_dataset(secondary_id)

        if not primary or not secondary:
            return None

        all_entries = primary.entries + secondary.entries

        for e in all_entries:
            if e.values is None:
                e.values = {}

        if remove_dupes:
            unique_map = {}
            for e in all_entries:
                key = (e.text.strip().lower(), e.label.lower())
                if key not in unique_map:
                    unique_map[key] = e
            merged_entries = list(unique_map.values())
        else:
            merged_entries = all_entries

        if new_dataset:
            info = getattr(self, "temp_new_dataset_info", None)
            if not info:
                raise ValueError("new_dataset=True but no dataset info provided.")

            new_id = uuid.uuid4()
            new_dataset_obj = DatasetBuilder(
                id=new_id,
                name=info.name,
                description=info.description,
                dataset_type=info.dataset_type,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                entries=merged_entries,
            )

            self.collection.insert_one(new_dataset_obj.to_dict())
            self.temp_new_dataset_info = None
            return new_dataset_obj

        primary.entries = merged_entries
        primary.updated_at = datetime.utcnow()

        self.collection.update_one(
            {"id": primary_id},
            {
                "$set": {
                    "entries": [e.to_dict() for e in merged_entries],
                    "updated_at": primary.updated_at.isoformat(),
                }
            }
        )

        return primary


