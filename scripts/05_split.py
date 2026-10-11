"""Usage: python scripts/05_split.py [--config configs/split.yaml]
Reads data/dedup/corpus.jsonl and writes data/splits/<target_lang>/{train,validation,test}.jsonl
(`none` = records without translation) plus reports/split_report.md."""
import argparse
import json
from pathlib import Path

import yaml

from darijabridge.dataset.report import write_split_report
from darijabridge.dataset.split import SPLITS, assign, summarize
from darijabridge.utils.io import read_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/split.yaml")
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    params = {k: cfg[k] for k in ("validation", "test", "salt")}

    by_task = assign(read_jsonl(cfg["input_file"]), **params)
    out_dir = Path(cfg["output_dir"])
    for task, splits in by_task.items():
        (out_dir / task).mkdir(parents=True, exist_ok=True)
        for split in SPLITS:
            with (out_dir / task / f"{split}.jsonl").open("w", encoding="utf-8") as f:
                for r in splits[split]:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = summarize(by_task)
    write_split_report(summary, params, cfg.get("report_dir", "reports"))

    print("\n=== Split summary ===")
    for task, sp in summary["tasks"].items():
        print(f"{task:5} " + "  ".join(f"{s}={sp[s]['records']:>6}" for s in SPLITS))
    print(f"\ngroups in several splits: {summary['groups_in_several_splits']} (must be 0)")
    print(f"Report: {cfg.get('report_dir', 'reports')}/split_report.md")


if __name__ == "__main__":
    main()
