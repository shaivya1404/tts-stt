#!/usr/bin/env python3
"""Minimal Conformer RNN-T training scaffold.

This script is intentionally lightweight and serves as a reference for how
production training code could be structured. Replace the dataset/model stubs
with real implementations before using it in a research setting.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import torch
from torch import Tensor, nn
from torch.utils.data import DataLoader, Dataset

try:
    import yaml
except ImportError as exc:  # pragma: no cover - executed only when dependency missing
    raise SystemExit("Please install PyYAML to run the STT training scripts (pip install pyyaml).") from exc

MODEL_BASE_PATH = Path(os.environ.get("MODEL_BASE_PATH", "/models"))


class STTDataset(Dataset):
    """Placeholder dataset that emits random tensors.

    TODO: Replace with a manifest-backed dataset that loads actual audio features
    and transcripts.
    """

    def __init__(self, manifest_path: str, sample_rate: int, fallback_size: int = 128) -> None:
        self.manifest_path = Path(manifest_path)
        self.sample_rate = sample_rate
        self.records = self._load_manifest(fallback_size)

    def _load_manifest(self, fallback_size: int) -> List[str]:
        if self.manifest_path.exists():
            with self.manifest_path.open("r", encoding="utf-8") as handle:
                return [line.strip() for line in handle if line.strip()]
        return [f"synthetic-utterance-{idx}" for idx in range(fallback_size)]

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.records)

    def __getitem__(self, index: int) -> Tuple[Tensor, Tensor]:
        _ = self.records[index]
        feature_dim = 256
        features = torch.randn(feature_dim)
        targets = torch.randn(feature_dim)
        return features, targets


class ConformerRNNT(nn.Module):
    """Tiny placeholder model emulating the Conformer + prediction network stack."""

    def __init__(self, input_dim: int = 256, hidden_dim: int = 512, output_dim: int = 256) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x: Tensor) -> Tensor:  # pragma: no cover - exercised via training loop
        return self.net(x)


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def create_dataloader(manifest_path: str, sample_rate: int, batch_size: int, shuffle: bool) -> DataLoader[Tuple[Tensor, Tensor]]:
    dataset = STTDataset(manifest_path, sample_rate)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader[Tuple[Tensor, Tensor]],
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
    grad_clip: float,
) -> float:
    model.train()
    total_loss = 0.0
    for batch_idx, (features, targets) in enumerate(loader):
        features = features.to(device)
        targets = targets.to(device)

        optimizer.zero_grad(set_to_none=True)
        outputs = model(features)
        loss = criterion(outputs, targets)
        loss.backward()
        if grad_clip > 0:
            nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()

        total_loss += loss.item()
        if batch_idx % 10 == 0:
            print(f"[train] step={batch_idx} loss={loss.item():.4f}")
    return total_loss / max(len(loader), 1)


def evaluate(model: nn.Module, loader: DataLoader[Tuple[Tensor, Tensor]], criterion: nn.Module, device: torch.device) -> float:
    model.eval()
    total_loss = 0.0
    with torch.no_grad():
        for features, targets in loader:
            features = features.to(device)
            targets = targets.to(device)
            outputs = model(features)
            loss = criterion(outputs, targets)
            total_loss += loss.item()
    return total_loss / max(len(loader), 1)


def save_checkpoint(model: nn.Module, optimizer: torch.optim.Optimizer, epoch: int, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / f"checkpoint-epoch-{epoch}.pt"
    torch.save({
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
    }, checkpoint_path)
    print(f"Saved checkpoint to {checkpoint_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Conformer RNNT placeholder")
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--device", choices=["cpu", "cuda"], default=None, help="Force training device")
    args = parser.parse_args()

    config = load_config(args.config)
    device_str = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(device_str)

    training_cfg = config.get("training", {})
    optimizer_cfg = config.get("optimizer", {})

    train_loader = create_dataloader(
        config.get("train_manifest", ""),
        config.get("sample_rate", 16000),
        training_cfg.get("batch_size", 8),
        shuffle=True,
    )
    val_loader = create_dataloader(
        config.get("val_manifest", ""),
        config.get("sample_rate", 16000),
        training_cfg.get("batch_size", 8),
        shuffle=False,
    )

    model = ConformerRNNT().to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=optimizer_cfg.get("lr", 5e-4),
        weight_decay=optimizer_cfg.get("weight_decay", 1e-5),
    )

    num_epochs = training_cfg.get("num_epochs", 5)
    grad_clip = training_cfg.get("grad_clip", 1.0)
    checkpoint_interval = config.get("output", {}).get("checkpoint_interval", 1)

    artifact_dir = MODEL_BASE_PATH / "stt" / config.get("model_name", "conformer_rnnt_indic") / config.get("version", "v1")
    artifact_dir.mkdir(parents=True, exist_ok=True)

    history: List[Dict[str, Any]] = []
    for epoch in range(1, num_epochs + 1):
        train_loss = train_one_epoch(model, train_loader, optimizer, criterion, device, grad_clip)
        val_loss = evaluate(model, val_loader, criterion, device)
        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})
        print(f"Epoch {epoch}/{num_epochs} train_loss={train_loss:.4f} val_loss={val_loss:.4f}")

        if epoch % checkpoint_interval == 0:
            save_checkpoint(model, optimizer, epoch, artifact_dir)

    final_model_path = artifact_dir / "conformer_rnnt.pt"
    torch.save(model.state_dict(), final_model_path)
    print(f"Saved final model to {final_model_path}")

    summary_path = artifact_dir / "training_summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump({"config": config, "history": history}, handle, indent=2)
    print(f"Wrote training summary to {summary_path}")


if __name__ == "__main__":
    main()
