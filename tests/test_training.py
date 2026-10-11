import json
import random

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

from darijabridge.training.data import collate
from darijabridge.training.loop import train


class FakeTokenizer:
    def save_pretrained(self, path):
        from pathlib import Path
        Path(path).mkdir(parents=True, exist_ok=True)
        (Path(path) / "tokenizer.txt").write_text("fake")


def tiny_model():
    from transformers import M2M100Config, M2M100ForConditionalGeneration
    cfg = M2M100Config(vocab_size=50, d_model=32, encoder_layers=1, decoder_layers=1,
                       encoder_attention_heads=2, decoder_attention_heads=2, encoder_ffn_dim=64,
                       decoder_ffn_dim=64, max_position_embeddings=64, pad_token_id=1, bos_token_id=0,
                       eos_token_id=2, decoder_start_token_id=2, dropout=0.0)
    return M2M100ForConditionalGeneration(cfg)


def toy_items(n=24, seed=0):
    rng = random.Random(seed)
    items = []
    for _ in range(n):
        x = [rng.randrange(3, 20) for _ in range(rng.randrange(3, 7))]
        items.append((x + [2], x[::-1] + [2]))            # learn to reverse a sequence
    return items


def test_collate_pads_inputs_and_masks_labels():
    b = collate([([5, 6, 2], [7, 2]), ([5, 2], [7, 8, 9, 2])], pad_id=1)
    assert b["input_ids"].tolist() == [[5, 6, 2], [5, 2, 1]]
    assert b["attention_mask"].tolist() == [[1, 1, 1], [1, 1, 0]]
    assert b["labels"].tolist() == [[7, 2, -100, -100], [7, 8, 9, 2]]


def test_training_loop_learns_and_saves(tmp_path):
    torch.manual_seed(0)
    items = toy_items()
    cfg = {"batch_size": 4, "grad_accum_steps": 2, "epochs": 40, "learning_rate": 3e-3, "fp16": False,
           "eval_every": 20, "log_every": 5, "seed": 1, "optimizer": "adamw"}
    result = train(tiny_model(), FakeTokenizer(), items, items, cfg, "cpu", 1, tmp_path)
    losses = [h["train_loss"] for h in result["history"] if "train_loss" in h]
    assert losses[-1] < losses[0] * 0.8
    assert (tmp_path / "best" / "config.json").exists() and (tmp_path / "last" / "config.json").exists()
    assert len((tmp_path / "train_log.jsonl").read_text().splitlines()) == len(result["history"])


def test_max_steps_stops_early_and_adafactor_runs(tmp_path):
    cfg = {"batch_size": 4, "epochs": 5, "max_steps": 3, "learning_rate": 1e-3, "fp16": False,
           "optimizer": "adafactor", "seed": 1}
    result = train(tiny_model(), FakeTokenizer(), toy_items(), toy_items(), cfg, "cpu", 1, tmp_path)
    assert result["steps"] == 3
