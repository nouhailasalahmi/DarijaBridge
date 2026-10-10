"""Usage: python scripts/02_clean.py [--config configs/cleaning.yaml]
Reads data/raw/<source>/<source>.jsonl, writes data/interim/ and reports/cleaning_report.md."""
import argparse
from pathlib import Path

import yaml

from darijabridge.cleaning.pipeline import run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/cleaning.yaml")
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    stats = run(cfg)

    print("\n=== Cleaning summary ===")
    for name, s in stats.items():
        print(f"{name:20} read={s['read']:>6} kept={s['kept']:>6} rejected={s['read'] - s['kept']:>6}")
    print(f"\nReport: {cfg.get('report_dir', 'reports')}/cleaning_report.md")


if __name__ == "__main__":
    main()
