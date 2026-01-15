#!/usr/bin/env python3
"""Whisper fine-tuning scaffold for the STT service."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict

import torch

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Please install PyYAML to run the STT training scripts (pip install pyyaml).") from exc

MODEL_BASE_PATH = Path(os.environ.get("MODEL_BASE_PATH", "/models"))


def load_transformer_deps():  # pragma: no cover - heavy imports only when training
    try:
        from transformers import AdamW, WhisperForConditionalGeneration, WhisperProcessor
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Install transformers + sentencepiece to fine-tune Whisper (pip install transformers sentencepiece)."
        ) from exc
    return AdamW, WhisperForConditionalGeneration, WhisperProcessor


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune Whisper placeholder")
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--device", choices=["cpu", "cuda"], default=None, help="Force training device")
    args = parser.parse_args()

    config = load_config(args.config)
    device_str = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(device_str)

    AdamW, WhisperForConditionalGeneration, WhisperProcessor = load_transformer_deps()

    base_model = config.get("base_model", "openai/whisper-small")
    processor = WhisperProcessor.from_pretrained(base_model)
    model = WhisperForConditionalGeneration.from_pretrained(base_model).to(device)

    training_cfg = config.get("training", {})
    optimizer = AdamW(model.parameters(), lr=training_cfg.get("learning_rate", 1e-5))
    num_epochs = training_cfg.get("num_epochs", 1)

    # TODO: Replace the synthetic batch below with a DataLoader built from
    #       the train/val manifests listed in the config. This placeholder simply
    #       exercises the optimizer so the script can run end-to-end.
    dummy_inputs = torch.randint(0, processor.tokenizer.vocab_size, (1, 128)).to(device)
    dummy_labels = dummy_inputs.clone()

    history = []
    for epoch in range(1, num_epochs + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        outputs = model(input_ids=dummy_inputs, labels=dummy_labels)
        loss = outputs.loss
        loss.backward()
        optimizer.step()
        history.append({"epoch": epoch, "loss": float(loss.detach().cpu())})
        print(f"Epoch {epoch}/{num_epochs} loss={loss.item():.4f}")

    whisper_dir = MODEL_BASE_PATH / "stt" / "whisper" / config.get("model_name", "whisper_indic") / config.get("version", "v1")
    whisper_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(whisper_dir)
    processor.save_pretrained(whisper_dir)

    summary_path = whisper_dir / "training_summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump({"config": config, "history": history}, handle, indent=2)
    print(f"Saved Whisper checkpoint + summary to {whisper_dir}")


if __name__ == "__main__":
    main()
