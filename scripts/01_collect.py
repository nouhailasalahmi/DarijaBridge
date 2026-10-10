"""Usage:
    python scripts/01_collect.py                      # all enabled sources
    python scripts/01_collect.py --only doda          # selected sources
A failing source does not stop the others; a summary is printed at the end.
"""
import argparse
from pathlib import Path

import yaml

from darijabridge.collection import COLLECTORS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/data_sources.yaml")
    parser.add_argument("--only", nargs="*", help="source names to run")
    args = parser.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    raw_dir = cfg.get("raw_dir", "data/raw")
    results = {}

    for name, scfg in cfg["sources"].items():
        if not scfg.get("enabled", True) or (args.only and name not in args.only):
            continue
        try:
            n = COLLECTORS[scfg["type"]](name, scfg, raw_dir).run()
            results[name] = ("OK", f"{n} records")
        except Exception as e:  # keep going with the other sources
            results[name] = ("FAILED", f"{type(e).__name__}: {e}")

    print("\n=== Collection summary ===")
    for name, (status, info) in results.items():
        print(f"{status:7} {name:20} {info}")
    if not results:
        print("No source ran (check `enabled` flags or --only).")


if __name__ == "__main__":
    main()