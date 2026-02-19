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
from dataset_builder.augmentation import TextAugmenter
from config_loader import ConfigLoader
from template.templateserviceimpl import TemplateServiceImpl
from template.utils.templategenerator import TemplateGenerator


class DatasetBuilderServiceImpl(DatasetBuilderService):
    def __init__(self, config_file: str = "config.json", augmentation_prob: float = 0.2):
        cfg = ConfigLoader(config_file).get_database_config()
        uri = f"mongodb://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['authSource']}"

        self.client = MongoClient(uri)
        self.db = self.client[cfg["name"]]
        self.collection = self.db["datasets"]
        self.template_service = TemplateServiceImpl()
        self.temp_new_dataset_info = None
        self.augmenter = TextAugmenter(prob=augmentation_prob)


    def create_dataset(self, name: str, description: str, dataset_type: DatasetType) -> DatasetBuilder:
        ds = DatasetBuilder.create(name, description, dataset_type)
        doc = ds.to_dict()
        result = self.collection.insert_one(doc)
        ds._id = str(result.inserted_id)
        return ds


    def add_entry(
            self,
            dataset_id: str,
            text: Optional[str],
            label: str,
            entry_type: EntryType = EntryType.MANUAL,
            template_id: Optional[str] = None,
            values: Optional[dict] = None,
            augment: bool = False
    ):
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return None

        now = datetime.utcnow()
        texts_to_add = []

        if entry_type == EntryType.TEMPLATE:
            if not template_id:
                raise ValueError("template_id is required for TEMPLATE entry type")

            tpl = self.template_service.get_template(template_id)
            if not tpl:
                return None

            if values and all(isinstance(v, str) for v in values.values()):
                base_text = tpl.pattern.format(**values)
                texts_to_add.append((base_text, values))
            else:
                dataset_values = {}
                for e in dataset.entries:
                    if e.values:
                        for k, v in e.values.items():
                            dataset_values.setdefault(k, set()).add(v)
                dataset_values = {k: list(v) for k, v in dataset_values.items()}

                generator = TemplateGenerator(tpl.pattern)
                input_values = values.get("values") if values and "values" in values else values
                variations = generator.generate_from_dataset_values(input_values or dataset_values)

                for var in variations:
                    texts_to_add.append((var["text"], var["values"]))

            final_entries = []

            for base_text, val in texts_to_add:
                final_entries.append(
                    DatasetEntry.create(
                        text=base_text,
                        label=label,
                        entry_type=EntryType.TEMPLATE,
                        template_id=template_id,
                        values=val or {}
                    )
                )

                if augment and base_text:
                    augmented = self.augmenter.augment(base_text)

                    if isinstance(augmented, list):
                        for aug in augmented:
                            if aug and aug != base_text:
                                final_entries.append(
                                    DatasetEntry.create(
                                        text=aug,
                                        label=label,
                                        entry_type=EntryType.TEMPLATE,
                                        template_id=template_id,
                                        values=val or {}
                                    )
                                )
                    elif augmented and augmented != base_text:
                        final_entries.append(
                            DatasetEntry.create(
                                text=augmented,
                                label=label,
                                entry_type=EntryType.TEMPLATE,
                                template_id=template_id,
                                values=val or {}
                            )
                        )

            if not final_entries:
                return None

            self.collection.update_one(
                {"id": dataset_id},
                {
                    "$push": {"entries": {"$each": [e.to_dict() for e in final_entries]}},
                    "$set": {"updated_at": now.isoformat()}
                }
            )

            return final_entries if len(final_entries) > 1 else final_entries[0]

        if not text and values and "text" in values:
            text = values["text"]

        if not text:
            return None

        final_entries = []

        final_entries.append(
            DatasetEntry.create(
                text=text,
                label=label,
                entry_type=EntryType.MANUAL,
                template_id=None,
                values={}
            )
        )

        if augment and text:
            augmented = self.augmenter.augment(text)

            if isinstance(augmented, list):
                for aug in augmented:
                    if aug and aug != text:
                        final_entries.append(
                            DatasetEntry.create(
                                text=aug,
                                label=label,
                                entry_type=EntryType.MANUAL,
                                template_id=None,
                                values={}
                            )
                        )
            elif augmented and augmented != text:
                final_entries.append(
                    DatasetEntry.create(
                        text=augmented,
                        label=label,
                        entry_type=EntryType.MANUAL,
                        template_id=None,
                        values={}
                    )
                )

        self.collection.update_one(
            {"id": dataset_id},
            {
                "$push": {"entries": {"$each": [e.to_dict() for e in final_entries]}},
                "$set": {"updated_at": now.isoformat()}
            }
        )

        return final_entries if len(final_entries) > 1 else final_entries[0]


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

    def add_entries_bulk(self, dataset_id: str, entries: List[dict], augment: bool = False) -> List[DatasetEntry]:
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

            texts_to_add = [text]

            if augment:
                augmented = self.augmenter.augment(text)


                if isinstance(augmented, list):
                    texts_to_add.extend(augmented)
                elif augmented:
                    texts_to_add.append(augmented)

            for t in texts_to_add:
                entry = DatasetEntry.create(
                    text=t,
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
            new_dataset: bool,
            augment: bool = False
    ) -> Optional[DatasetBuilder]:
        primary = self.get_dataset(primary_id)
        secondary = self.get_dataset(secondary_id)

        if not primary or not secondary:
            return None

        all_entries = primary.entries + secondary.entries

        for e in all_entries:
            if e.values is None:
                e.values = {}
            if augment and e.text:
                e.text = self.augmenter.augment(e.text)

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


    def augment_entries(self, dataset_id: str, num_augmentations: int = 1) -> List[DatasetEntry]:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return []

        augmented_entries = []
        now = datetime.utcnow()

        for entry in dataset.entries:
            for _ in range(num_augmentations):
                augmented_text = self.augmenter.augment(entry.text)
                new_entry = DatasetEntry.create(
                    text=augmented_text,
                    label=entry.label,
                    entry_type=EntryType.MANUAL,
                    template_id=None,
                    values={}
                )
                augmented_entries.append(new_entry)

        if augmented_entries:
            self.collection.update_one(
                {"id": dataset_id},
                {
                    "$push": {"entries": {"$each": [e.to_dict() for e in augmented_entries]}},
                    "$set": {"updated_at": now.isoformat()}
                }
            )

        return augmented_entries


