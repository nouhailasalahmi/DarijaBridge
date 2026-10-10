import json
from collections import Counter
from pathlib import Path

from darijabridge.cleaning.alignment import check_pair
from darijabridge.cleaning.dedup import Deduper
from darijabridge.cleaning.filters import check_text
from darijabridge.cleaning.report import write_report
from darijabridge.cleaning.text_ops import clean_text
from darijabridge.utils.io import read_jsonl
from darijabridge.utils.logging import get_logger

log = get_logger("cleaning")


def _clean_record(rec: dict, steps, f) -> tuple[dict | None, str | None, list[str]]:
    """Returns (cleaned_record, reject_reason, modified_steps)."""
    darija, ch1 = clean_text(rec["text_darija"], steps)
    reason = check_text(darija, f)
    if reason:
        return None, reason, ch1

    target, ch2 = rec.get("text_target"), []
    if target:
        target, ch2 = clean_text(target, steps)
        reason = check_text(target, f)
        if reason:
            return None, "bad_target", ch1 + ch2
        reason = check_pair(darija, target, f)
        if reason:
            return None, reason, ch1 + ch2

    out = dict(rec, text_darija=darija, text_target=target or None)
    if not target:
        out["target_lang"] = None
    return out, None, ch1 + ch2


def run(cfg: dict) -> dict:
    in_dir, out_dir = Path(cfg["input_dir"]), Path(cfg["output_dir"])
    steps, f = cfg.get("steps"), cfg.get("filters", {})
    sources = cfg.get("sources") or sorted(p.name for p in in_dir.iterdir() if p.is_dir())
    dedup, stats = Deduper(), {}
    (out_dir / "rejected").mkdir(parents=True, exist_ok=True)

    for source in sources:
        src_file = in_dir / source / f"{source}.jsonl"
        if not src_file.exists():
            log.warning("skip %s: %s not found", source, src_file)
            continue
        s = {"read": 0, "kept": 0, "with_target": 0, "rejected": Counter(), "modified": Counter()}
        with (out_dir / f"{source}.jsonl").open("w", encoding="utf-8") as kept, \
             (out_dir / "rejected" / f"{source}.jsonl").open("w", encoding="utf-8") as rejected:
            for rec in read_jsonl(src_file):
                s["read"] += 1
                out, reason, changed = _clean_record(rec, steps, f)
                s["modified"].update(changed)
                if out and not reason:
                    reason = dedup.check(source, out["text_darija"], out["text_target"])
                if reason:
                    s["rejected"][reason] += 1
                    rejected.write(json.dumps(
                        {"id": rec["id"], "source": source, "reason": reason,
                         "text_darija": rec["text_darija"], "text_target": rec.get("text_target")},
                        ensure_ascii=False) + "\n")
                    continue
                s["kept"] += 1
                s["with_target"] += bool(out["text_target"])
                kept.write(json.dumps(out, ensure_ascii=False) + "\n")
        s["rejected"], s["modified"] = dict(s["rejected"]), dict(s["modified"])
        stats[source] = s
        log.info("%s: %d read, %d kept", source, s["read"], s["kept"])

    write_report(stats, cfg.get("report_dir", "reports"))
    return stats
