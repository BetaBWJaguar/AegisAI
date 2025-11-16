# -*- coding: utf-8 -*-
from typing import List, Optional, Dict
from dataset_builder.dataset_builder_serviceimpl import DatasetBuilderServiceImpl
from dataset_builder.entrytype import EntryType


class ScrapperDatasetIntegrator:
    def __init__(self, config_path: str):
        self.dataset_service = DatasetBuilderServiceImpl(config_path)

    def integrate(
            self,
            dataset_id: str,
            scrapped_data: List[Dict[str, str]],
            entry_type: EntryType = EntryType.MANUAL,
            label: Optional[str] = None,
            template_id: Optional[str] = None,
            values: Optional[Dict[str, str]] = None
    ) -> List[Dict]:

        if not scrapped_data:
            return []

        added_entries = []

        if entry_type == EntryType.MANUAL:
            for post in scrapped_data:
                entry = self.dataset_service.add_entry(
                    dataset_id=dataset_id,
                    text=post.get("text", ""),
                    label=label or "SCRAPPED_MANUAL",
                    entry_type=EntryType.MANUAL
                )
                if entry:
                    added_entries.append(entry.to_dict())

        elif entry_type == EntryType.TEMPLATE:
            for post in scrapped_data:
                entry = self.dataset_service.add_entry(
                    dataset_id=dataset_id,
                    text=post.get("text", ""),
                    label=label or "SCRAPPED_TEMPLATE",
                    entry_type=EntryType.TEMPLATE,
                    template_id=template_id,
                    values=values or post.get("values", {})
                )
                if entry:
                    if isinstance(entry, list):
                        added_entries.extend([e.to_dict() for e in entry])
                    else:
                        added_entries.append(entry.to_dict())

        return added_entries
