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

                scraped_text = post.get("text", "")
                if not scraped_text:
                    continue

                template = self.dataset_service.template_service.get_template(template_id)
                pattern = template.pattern

                placeholders = extract_placeholders(pattern)

                user_values = values or {}

                matched_values = {}

                for ph in placeholders:

                    if ph in user_values:

                        possible_values = user_values[ph]

                        if isinstance(possible_values, list):
                            matched = None
                            for v in possible_values:
                                if v.lower() in scraped_text.lower():
                                    matched = v
                                    break

                            if matched:
                                matched_values[ph] = matched
                            else:
                                matched_values = None
                                break
                        else:
                            if possible_values.lower() in scraped_text.lower():
                                matched_values[ph] = possible_values
                            else:
                                matched_values = None
                                break

                    else:
                        matched_values = None
                        break

                if matched_values is None:
                    continue

                entry = self.dataset_service.add_entry(
                    dataset_id=dataset_id,
                    text=scraped_text,
                    label=label or "SCRAPPED_TEMPLATE",
                    entry_type=EntryType.TEMPLATE,
                    template_id=template_id,
                    values=matched_values
                )

                if entry:
                    if isinstance(entry, list):
                        for e in entry:
                            added_entries.append(e.to_dict())
                    else:
                        added_entries.append(entry.to_dict())



        return added_entries
