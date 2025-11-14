# -*- coding: utf-8 -*-
from typing import List, Dict, Any
from pathlib import Path
import shutil

from transformers import (
    BertForMaskedLM,
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments
)
from datasets import load_dataset, Dataset

from trainer.trainer_utils import (
    train_tokenizer,
    prepare_bert_config,
    load_hf_tokenizer,
    load_text_datasets,
    tokenize_dataset,
    create_data_collator,
    create_training_args,
    create_trainer,
    save_trained_model,
)
from trainer.service.trainer_service import TrainerService
from dataset_builder.dataset_builder_serviceimpl import DatasetBuilderServiceImpl


class TrainerServiceImpl(TrainerService):
    def __init__(self, config_file: str = "config.json"):
        self.dataset_service = DatasetBuilderServiceImpl(config_file)

    def train_language_model(
            self,
            corpus_files: List[str],
            output_dir: str,
            model_size: str
    ) -> Dict[str, Any]:
        vocab_path = train_tokenizer(corpus_files, output_dir + "/tokenizer")

        hf_tokenizer = load_hf_tokenizer(vocab_path)
        config = prepare_bert_config(
            vocab_size=len(hf_tokenizer.get_vocab()),
            model_size=model_size
        )
        model = BertForMaskedLM(config)

        dataset = load_text_datasets(corpus_files)
        tokenized_ds = tokenize_dataset(dataset, hf_tokenizer)

        data_collator = create_data_collator(hf_tokenizer)
        args = create_training_args(output_dir)

        trainer = create_trainer(model, args, tokenized_ds, data_collator)
        trainer.train()

        save_trained_model(trainer, output_dir, hf_tokenizer)

        return {
            "status": "success",
            "type": "base_language_model",
            "trained_vocab_size": len(hf_tokenizer.get_vocab()),
            "model_size": model_size,
            "output_dir": output_dir
        }


    def fine_tune_model(
            self,
            model_path: str,
            dataset_id: str,
            output_dir: str,
            training_args: TrainingArguments,
    ) -> Dict[str, Any]:

        dataset = self.dataset_service.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset '{dataset_id}' not found in database.")
        if not dataset.entries:
            raise ValueError(f"Dataset '{dataset_id}' has no entries.")

        valid_entries = [(e.text, e.label) for e in dataset.entries if e.text and e.label is not None]
        texts = [t for t, l in valid_entries]
        labels = [l for t, l in valid_entries]

        unique_labels = sorted(set(labels))
        label2id = {label: i for i, label in enumerate(unique_labels)}
        id2label = {v: k for k, v in label2id.items()}
        y = [label2id[label] for label in labels]

        num_labels = len(unique_labels)

        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_path,
            num_labels=num_labels,
            id2label=id2label,
            label2id=label2id
        )

        ds = Dataset.from_dict({"text": texts, "label": y})
        tokenized_ds = ds.map(
            lambda e: tokenizer(
                e["text"],
                truncation=True,
                padding="max_length",
                max_length=128
            ),
            batched=True
        )

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_ds
        )

        trainer.train()

        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)

        return {
            "status": "success",
            "source": "mongodb",
            "type": "fine_tune",
            "dataset_name": dataset.name,
            "dataset_id": dataset_id,
            "labels": label2id,
            "output_dir": output_dir
        }

