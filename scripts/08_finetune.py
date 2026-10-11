"""Fine-tunes NLLB on the train split.

  python scripts/08_finetune.py --max-steps 20 --output-dir models/smoke      # quick check
  python scripts/08_finetune.py                                                # full run (use a GPU)
  python scripts/08_finetune.py --train-file /kaggle/input/<dataset>/en/train.jsonl \
        --validation-file /kaggle/input/<dataset>/en/validation.jsonl --output-dir /kaggle/working/ft_norm

Then evaluate with the SAME script and test split as the baseline:
  python scripts/06_baseline.py --model models/nllb600m_ft_norm/best --name ft_norm_test
"""
import argparse
import json
import platform
from collections import Counter
from pathlib import Path

import yaml

from darijabridge.evaluation.sampling import stratified_sample
from darijabridge.training.data import load_pairs, tokenize_pairs
from darijabridge.training.loop import train
from darijabridge.utils.io import read_jsonl
from darijabridge.utils.logging import get_logger

log = get_logger("finetune")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/finetune.yaml")
    for opt, typ in (("--train-file", str), ("--validation-file", str), ("--output-dir", str),
                     ("--input-field", str), ("--max-steps", int), ("--epochs", int), ("--batch-size", int)):
        ap.add_argument(opt, type=typ)
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    for key in ("train_file", "validation_file", "output_dir", "input_field", "max_steps", "epochs", "batch_size"):
        val = getattr(args, key)
        if val is not None:
            cfg[key] = val

    import torch
    import transformers
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        log.warning("No GPU found: fine for a smoke test (--max-steps 20), far too slow for a full run.")

    tokenizer = AutoTokenizer.from_pretrained(cfg["model"], src_lang=cfg["src_lang"], tgt_lang=cfg["tgt_lang"])
    model = AutoModelForSeq2SeqLM.from_pretrained(cfg["model"]).to(device)

    train_records = list(read_jsonl(cfg["train_file"]))
    if cfg.get("train_per_source_cap"):
        train_records = stratified_sample(train_records, cfg["train_per_source_cap"])
    val_records = stratified_sample(list(read_jsonl(cfg["validation_file"])), cfg.get("eval_per_source"))
    train_pairs = load_pairs(train_records, cfg["input_field"])
    val_pairs = load_pairs(val_records, cfg["input_field"])
    counts = {"train": dict(Counter(p[2] for p in train_pairs)), "validation": dict(Counter(p[2] for p in val_pairs))}
    log.info("pairs: %s", counts)

    train_items = tokenize_pairs(tokenizer, train_pairs, cfg["max_length"])
    val_items = tokenize_pairs(tokenizer, val_pairs, cfg["max_length"])
    result = train(model, tokenizer, train_items, val_items, cfg, device, tokenizer.pad_token_id, cfg["output_dir"])

    summary = {k: v for k, v in result.items() if k != "history"}
    summary.update(config=cfg, pairs=counts, device=device,
                   versions={"python": platform.python_version(), "torch": torch.__version__,
                             "transformers": transformers.__version__})
    out = Path(cfg["output_dir"])
    (out / "train_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDone: {summary['steps']} steps in {summary['seconds']} s, best validation loss {summary['best_val_loss']}")
    print(f"Models: {out}/best and {out}/last   Summary: {out}/train_summary.json")


if __name__ == "__main__":
    main()
