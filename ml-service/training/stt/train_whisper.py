#!/usr/bin/env python3
"""Whisper fine-tuning skeleton for STT."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

import torch
import yaml

try:
    from datasets import Audio, load_dataset
    from transformers import Trainer, TrainingArguments, WhisperForConditionalGeneration, WhisperProcessor
except ImportError as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "Whisper training requires `datasets` and `transformers`. Install them via `pip install datasets transformers`."
    ) from exc

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from common import settings  # noqa: E402  # pylint: disable=wrong-import-position


def load_config(config_path: Path) -> Dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def prepare_dataset(manifest: Path, sample_rate: int, audio_column: str) -> Any:
    dataset = load_dataset("json", data_files={"data": str(manifest)})
    dataset = dataset["data"].cast_column(audio_column, Audio(sampling_rate=sample_rate))
    return dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune Whisper on Indic manifests")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--device", default=None, help="Optional torch device override (cpu/cuda)")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    sample_rate = int(config.get("sample_rate", 16000))
    audio_column = config.get("audio_column", "audio_filepath")
    text_column = config.get("text_column", "text")

    processor = WhisperProcessor.from_pretrained(config["base_model"])
    model = WhisperForConditionalGeneration.from_pretrained(config["base_model"])

    train_dataset = prepare_dataset(Path(config["train_manifest"]), sample_rate, audio_column)
    eval_dataset = prepare_dataset(Path(config["val_manifest"]), sample_rate, audio_column)

    def preprocess(batch: Dict[str, Any]) -> Dict[str, Any]:  # noqa: D401 - inline helper
        audio = batch[audio_column]
        inputs = processor(
            audio=audio["array"],
            sampling_rate=audio["sampling_rate"],
            text=batch[text_column],
            return_tensors="pt",
        )
        batch["input_features"] = inputs["input_features"][0]
        batch["labels"] = inputs["labels"][0]
        return batch

    train_processed = train_dataset.map(preprocess, remove_columns=train_dataset.column_names)
    eval_processed = eval_dataset.map(preprocess, remove_columns=eval_dataset.column_names)

    output_dir = Path(settings.model_base_path) / "stt" / "whisper" / config["model_name"] / config["version"]
    output_dir.mkdir(parents=True, exist_ok=True)

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    model.to(torch.device(device))
    print(f"Using device: {device}")

    training_args = TrainingArguments(
        output_dir=str(output_dir / "checkpoints"),
        per_device_train_batch_size=config["training"].get("batch_size", 4),
        per_device_eval_batch_size=config["training"].get("batch_size", 4),
        learning_rate=float(config["training"].get("learning_rate", 1e-5)),
        num_train_epochs=int(config["training"].get("epochs", 3)),
        logging_steps=int(config["training"].get("log_every_n_steps", 50)),
        gradient_accumulation_steps=int(config["training"].get("gradient_accumulation_steps", 1)),
        evaluation_strategy="steps",
        eval_steps=config["training"].get("log_every_n_steps", 50),
        save_steps=config.get("output", {}).get("save_every_n_steps", 1000),
        fp16=True,
        push_to_hub=config.get("output", {}).get("push_to_hub", False),
    )

    def collate_fn(examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        padded = processor.feature_extractor.pad(
            [{"input_features": example["input_features"]} for example in examples],
            return_tensors="pt",
        )
        label_tensors = [torch.tensor(example["labels"], dtype=torch.long) for example in examples]
        padded_labels = torch.nn.utils.rnn.pad_sequence(label_tensors, batch_first=True, padding_value=-100)
        padded["labels"] = padded_labels
        return padded

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_processed,
        eval_dataset=eval_processed,
        tokenizer=processor.tokenizer,
        data_collator=collate_fn,
    )

    trainer.train()
    trainer.save_model(output_dir)
    processor.save_pretrained(output_dir)
    print(f"Whisper fine-tuned checkpoints saved to {output_dir}")


if __name__ == "__main__":
    main()
