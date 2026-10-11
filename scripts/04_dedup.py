"""Usage: python scripts/04_dedup.py [--config configs/dedup.yaml]
Reads data/processed/<source>.jsonl, writes data/dedup/corpus.jsonl (all kept records, with a
`group_id`), data/dedup/rejected.jsonl and reports/dedup_report.md."""
import argparse
import json
from pathlib import Path

import yaml

from darijabridge.dataset.dedup import deduplicate
from darijabridge.dataset.report import write_dedup_report
from darijabridge.utils.io import read_jsonl
from darijabridge.utils.logging import get_logger

log = get_logger("dedup")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/dedup.yaml")
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    in_dir, out_dir = Path(cfg["input_dir"]), Path(cfg["output_dir"])
    sources = {}
    for name in cfg["sources"]:
        path = in_dir / f"{name}.jsonl"
        if path.exists():
            sources[name] = read_jsonl(path)
        else:
            log.warning("skip %s: %s not found", name, path)

    kept, rejected, summary = deduplicate(sources)

    out_dir.mkdir(parents=True, exist_ok=True)
    for fname, rows in (("corpus.jsonl", kept), ("rejected.jsonl", rejected)):
        with (out_dir / fname).open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    write_dedup_report(summary, cfg.get("report_dir", "reports"))
    print("\n=== Deduplication summary ===")
    for name, s in summary["sources"].items():
        print(f"{name:20} read={s['read']:>6} kept={s['kept']:>6} rejected={s['read'] - s['kept']:>6}")
    print(f"\nkept={summary['kept']}  groups={summary['groups']}  "
          f"groups with several records={summary['groups_with_several_records']}")
    print(f"Report: {cfg.get('report_dir', 'reports')}/dedup_report.md")


if __name__ == "__main__":
    main()
