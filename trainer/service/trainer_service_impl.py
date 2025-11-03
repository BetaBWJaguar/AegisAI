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
    save_trained_model
)
from trainer.service.trainer_service import TrainerService
from dataset_builder.dataset_builder_serviceimpl import DatasetBuilderServiceImpl


class TrainerServiceImpl(TrainerService):
    def __init__(self, config_file: str = "config.json"):
        self.dataset_service = DatasetBuilderServiceImpl(config_file)

    def train_language_model(self, corpus_files: List[str], output_dir: str) -> Dict[str, Any]:
        vocab_path = train_tokenizer(corpus_files, output_dir + "/tokenizer")

        hf_tokenizer = load_hf_tokenizer(vocab_path)
        config = prepare_bert_config(vocab_size=len(hf_tokenizer.get_vocab()))
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
            "source": "huggingface",
            "type": "base_language_model",
            "trained_vocab_size": len(hf_tokenizer.get_vocab()),
            "output_dir": output_dir
        }

    def fine_tune_model(self, model_path: str, dataset_id: str, output_dir: str, num_labels: int = 2) -> Dict[str, Any]:
        dataset = self.dataset_service.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset '{dataset_id}' not found in database.")
        if not dataset.entries:
            raise ValueError(f"Dataset '{dataset_id}' has no entries.")

        texts = [e.text for e in dataset.entries if e.text]
        labels = [e.label for e in dataset.entries if e.label]

        unique_labels = sorted(set(labels))
        label2id = {label: i for i, label in enumerate(unique_labels)}
        y = [label2id[label] for label in labels]

        data_dir = Path(output_dir) / "finetune_data"
        data_dir.mkdir(parents=True, exist_ok=True)
        data_file = data_dir / "train.txt"

        try:
            with open(data_file, "w", encoding="utf-8") as f:
                for text in texts:
                    f.write(text.strip().replace("\n", " ") + "\n")

            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=num_labels)

            ds = Dataset.from_dict({"text": texts, "label": y})
            tokenized_ds = ds.map(lambda e: tokenizer(e["text"], truncation=True, padding="max_length", max_length=128),
                                  batched=True)

            args = TrainingArguments(
                output_dir=output_dir,
                per_device_train_batch_size=8,
                num_train_epochs=3,
                save_total_limit=2
            )

            trainer = Trainer(model=model, args=args, train_dataset=tokenized_ds)
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

        finally:
            if data_dir.exists():
                shutil.rmtree(data_dir, ignore_errors=True)
