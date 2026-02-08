# -*- coding: utf-8 -*-
from typing import List, Optional, Dict
from dataset_builder.dataset_builder_serviceimpl import DatasetBuilderServiceImpl
from dataset_builder.entrytype import EntryType
from template.utils.extract_placeholders import extract_placeholders


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
            values: Optional[Dict[str, List[str]]] = None
    ) -> List[Dict]:

        if not scrapped_data:
            return []

        added_entries: List[Dict] = []
        label = label or ("SCRAPPED_TEMPLATE" if entry_type == EntryType.TEMPLATE else "SCRAPPED_MANUAL")

        if entry_type == EntryType.MANUAL:
            for post in scrapped_data:
                text = post.get("text", "")
                if not text:
                    continue
                entry = self.dataset_service.add_entry(
                    dataset_id=dataset_id,
                    text=text,
                    label=label,
                    entry_type=EntryType.MANUAL
                )
                if entry:
                    added_entries.append(entry.to_dict())

        elif entry_type == EntryType.TEMPLATE:
            if not template_id:
                return []

            template = self.dataset_service.template_service.get_template(template_id)
            if not template:
                return []

            pattern = template.pattern
            placeholders = extract_placeholders(pattern)
            user_values = values or {}

            for post in scrapped_data:
                scraped_text = post.get("text", "")
                if not scraped_text:
                    continue

                scraped_lower = scraped_text.lower()
                matched_values = {}

                for ph in placeholders:
                    possible_values = user_values.get(ph)
                    if not possible_values:
                        matched_values = None
                        break

                    if isinstance(possible_values, list):
                        match = next((v for v in possible_values if v.lower() in scraped_lower), None)
                        if not match:
                            matched_values = None
                            break
                        matched_values[ph] = match
                    else:
                        if possible_values.lower() not in scraped_lower:
                            matched_values = None
                            break
                        matched_values[ph] = possible_values

                if not matched_values:
                    continue

                entry = self.dataset_service.add_entry(
                    dataset_id=dataset_id,
                    text=scraped_text,
                    label=label,
                    entry_type=EntryType.TEMPLATE,
                    template_id=template_id,
                    values=matched_values
                )

                if entry:
                    if isinstance(entry, list):
                        added_entries.extend(e.to_dict() for e in entry)
                    else:
                        added_entries.append(entry.to_dict())



        return added_entries
