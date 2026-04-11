# -*- coding: utf-8 -*-
import random
from typing import List, Dict, Any, Optional
import numpy as np
import torch

from transformers import (
    BertForMaskedLM,
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
    EvalPrediction,
)
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from datasets import Dataset, ClassLabel

from config_loader import ConfigLoader
from trainer.trainer_utils import (
    train_tokenizer,
    prepare_bert_config,
    load_hf_tokenizer,
    load_text_datasets,
    tokenize_dataset,
    create_data_collator,
    create_training_args,
    create_trainer,
    save_trained_model, load_model_sizes,
)
from trainer.service.trainer_service import TrainerService
from dataset_builder.dataset_builder_serviceimpl import DatasetBuilderServiceImpl
from profanity.categories.profanity_categories import ProfanityCategories
from profanity.categories.profanity_categories_util import build_label
from profanity.categories.profanity_label_validator import ProfanityLabelValidator
from profanity.categories.label_encoder import LabelEncoder


def compute_metrics(pred: EvalPrediction) -> Dict[str, float]:
    logits = pred.predictions
    labels = pred.label_ids
    preds = np.argmax(logits, axis=1)

    return {
        "accuracy": float(accuracy_score(labels, preds)),
        "precision_macro": float(precision_score(labels, preds, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(labels, preds, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(labels, preds, average="macro", zero_division=0)),
        "precision_weighted": float(precision_score(labels, preds, average="weighted", zero_division=0)),
        "recall_weighted": float(recall_score(labels, preds, average="weighted", zero_division=0)),
        "f1_weighted": float(f1_score(labels, preds, average="weighted", zero_division=0)),
    }


class TrainerServiceImpl(TrainerService):
    def __init__(self, config_file: str = "config.json"):
        self.dataset_service = DatasetBuilderServiceImpl(config_file)
        self.config_loader = ConfigLoader(config_file)
        self.trainer_config = self.config_loader.get_trainer_config()

    @staticmethod
    def _device_info() -> Dict[str, Any]:
        cuda = torch.cuda.is_available()
        info = {"cuda": cuda, "device": "cuda" if cuda else "cpu"}
        if cuda:
            try:
                info["gpu_name"] = torch.cuda.get_device_name(0)
            except Exception:
                info["gpu_name"] = "unknown"
        return info

    def _get_model_sizes_path(self) -> str:
        path = self.trainer_config.get("model_sizes_path")
        if not path:
            raise ValueError("Path is not found!")
        return path

    @staticmethod
    def _validate_model_size(model_size: str) -> None:
        allowed = {"tiny", "small", "base", "large"}
        if model_size not in allowed:
            raise ValueError(f"Invalid model_size='{model_size}'. Allowed: {sorted(list(allowed))}")

    @staticmethod
    def _merge_training_args(user_args: Optional[Dict[str, Any]], output_dir: str) -> TrainingArguments:

        user_args = dict(user_args or {})

        cuda = torch.cuda.is_available()

        bf16 = bool(user_args.get("bf16", False))
        fp16 = bool(user_args.get("fp16", cuda and not bf16))

        defaults = {
            "output_dir": output_dir,
            "overwrite_output_dir": True,
            "num_train_epochs": 3,
            "per_device_train_batch_size": 8,
            "per_device_eval_batch_size": 8,
            "learning_rate": 5e-5,
            "weight_decay": 0.01,
            "warmup_ratio": 0.0,
            "logging_steps": 25,
            "metric_for_best_model": "f1_macro",
            "greater_is_better": True,
            "report_to": [],
            "fp16": fp16,
            "bf16": bf16,
        }

        merged = {**defaults, **user_args}
        return TrainingArguments(**merged)

    def train_language_model(
            self,
            corpus_files: List[str],
            output_dir: str,
            model_size: str
    ) -> Dict[str, Any]:
        vocab_path = train_tokenizer(corpus_files, output_dir + "/tokenizer")

        hf_tokenizer = load_hf_tokenizer(vocab_path)
        model_sizes = load_model_sizes(
            self._get_model_sizes_path()
        )
        config = prepare_bert_config(
            vocab_size=len(hf_tokenizer.get_vocab()),
            model_size=model_size,
            model_sizes=model_sizes
        )
        model = BertForMaskedLM(config)

        dataset = load_text_datasets(corpus_files)
        tokenized_ds = tokenize_dataset(dataset, hf_tokenizer,128)

        data_collator = create_data_collator(hf_tokenizer)
        args = create_training_args(output_dir)

        random.seed(42)
        np.random.seed(42)
        torch.manual_seed(42)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(42)

        trainer = create_trainer(model, args, tokenized_ds, data_collator)

        dev = self._device_info()
        print("[Trainer] Device:", dev)

        if dev["cuda"]:
            model.to("cuda")

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
            training_args: Dict[str, Any],
    ) -> Dict[str, Any]:
        dataset = self.dataset_service.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset '{dataset_id}' not found in database.")
        if not dataset.entries:
            raise ValueError(f"Dataset '{dataset_id}' has no entries.")

        dataset_dict = [e.to_dict() for e in dataset.entries]
        profanity_categories = ProfanityCategories()
        profanity_categories.build_from_dataset(dataset_dict)
        
        validator = ProfanityLabelValidator(profanity_categories)
        is_valid, invalid_rows = validator.validate_dataset(dataset_dict)
        if not is_valid:
            raise ValueError(f"Dataset '{dataset_id}' contains invalid labels. Invalid rows: {invalid_rows}")

        valid_entries = []
        for e in dataset.entries:
            if e.text and e.label is not None:
                combined_label = build_label(e.label, e.sublabel)
                valid_entries.append((e.text, combined_label))

        random.seed(42)
        random.shuffle(valid_entries)

        texts = [t for t, _ in valid_entries]
        labels = [l for _, l in valid_entries]

        label_encoder = LabelEncoder(profanity_categories)
        label_encoder.fit()
        label2id = label_encoder.mapping
        id2label = label_encoder.reverse_mapping
        y = label_encoder.encode_batch(labels)
        unique_labels = label_encoder.labels
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_path,
            num_labels=len(unique_labels),
            id2label=id2label,
            label2id=label2id
        )

        model.config.id2label = id2label
        model.config.label2id = label2id

        ds = Dataset.from_dict({"text": texts, "label": y})
        ds = ds.cast_column("label", ClassLabel(num_classes=len(unique_labels), names=unique_labels))

        tokenized_ds = ds.map(
            lambda e: tokenizer(
                e["text"],
                truncation=True,
                padding="max_length",
                max_length=128
            ),
            batched=True,
            desc="Tokenizing"
        )

        try:
            split = tokenized_ds.train_test_split(
                test_size=0.1,
                seed=42,
                stratify_by_column="label"
            )
        except Exception:
            split = tokenized_ds.train_test_split(
                test_size=0.1,
                seed=42
            )

        args = self._merge_training_args(training_args, output_dir=output_dir)
        data_collator = DataCollatorWithPadding(tokenizer)

        dev = self._device_info()
        print("[Trainer] Device:", dev)

        trainer = Trainer(
            model=model,
            args=args,
            train_dataset=split["train"],
            eval_dataset=split["test"],
            data_collator=data_collator,
            compute_metrics=compute_metrics
        )

        trainer.train()
        metrics = trainer.evaluate()

        trainer.save_model(output_dir)
        # noinspection PyUnresolvedReferences
        trainer.save_state()
        tokenizer.save_pretrained(output_dir)

        return {
            "status": "success",
            "source": "mongodb",
            "type": "fine_tune",
            "dataset_name": dataset.name,
            "dataset_id": dataset_id,
            "labels": label2id,
            "metrics": metrics,
            "output_dir": output_dir
        }

