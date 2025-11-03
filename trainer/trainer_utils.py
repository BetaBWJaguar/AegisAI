# -*- coding: utf-8 -*-
from pathlib import Path
from typing import List, Dict, Any
from tokenizers.implementations import BertWordPieceTokenizer
from transformers import (
    BertConfig,
    BertTokenizerFast,
    BertForMaskedLM,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
)
from datasets import load_dataset


def train_tokenizer(
        corpus_files: List[str],
        output_dir: str,
        vocab_size: int = 40000,
        min_frequency: int = 2,
        lowercase: bool = True
) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    tokenizer = BertWordPieceTokenizer(lowercase=lowercase)
    tokenizer.train(files=corpus_files, vocab_size=vocab_size, min_frequency=min_frequency)
    tokenizer.save_model(output_dir)
    return str(Path(output_dir) / "vocab.txt")


def prepare_bert_config(vocab_size: int) -> BertConfig:
    return BertConfig(
        vocab_size=vocab_size,
        hidden_size=512,
        num_hidden_layers=4,
        num_attention_heads=4,
        intermediate_size=1024,
        max_position_embeddings=512,
        type_vocab_size=1,
        add_pooling_layer=True,
        tie_word_embeddings=True
    )


def load_hf_tokenizer(vocab_file: str) -> BertTokenizerFast:
    return BertTokenizerFast(vocab_file=vocab_file)


def load_text_datasets(corpus_files: List[str]):
    return load_dataset("text", data_files={"train": corpus_files})


def tokenize_dataset(dataset, tokenizer, max_length: int = 64):
    def tokenize_fn(batch):
        return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=max_length)
    dataset = dataset.map(tokenize_fn, batched=True, remove_columns=["text"])
    dataset.set_format("torch")
    return dataset


def create_data_collator(tokenizer):
    return DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=True,
        mlm_probability=0.15,
    )


def create_training_args(
        output_dir: str,
        epochs: int = 5,
        batch_size: int = 32,
        save_steps: int = 2000,
        logging_steps: int = 500
) -> TrainingArguments:
    return TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        per_device_train_batch_size=batch_size,
        num_train_epochs=epochs,
        save_steps=save_steps,
        save_total_limit=2,
        prediction_loss_only=True,
        logging_steps=logging_steps,
        fp16=True,
    )


def create_trainer(model, args, dataset, data_collator):
    return Trainer(
        model=model,
        args=args,
        train_dataset=dataset["train"],
        data_collator=data_collator
    )


def save_trained_model(trainer: Trainer, output_dir: str, tokenizer: BertTokenizerFast):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    return output_dir
