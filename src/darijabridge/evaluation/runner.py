"""Runs a translator on a test set and scores it, overall and per source."""
from collections import defaultdict
from statistics import mean

from darijabridge.evaluation.metrics import bootstrap_ci, score
from darijabridge.evaluation.sampling import stratified_sample


def run_baseline(records: list[dict], translator, input_field: str, per_source: int | None = None,
                 bootstrap: int = 200, sources: list[str] | None = None) -> tuple[list[dict], dict]:
    """Returns (predictions, metrics). Records without the input field or without a reference are
    skipped and counted (e.g. the reference Arabic text only exists for DODA)."""
    skipped = defaultdict(int)
    usable = []
    for r in records:
        if sources and r["source"] not in sources:
            continue
        if not r.get(input_field) or not r.get("text_target"):
            skipped[r["source"]] += 1
            continue
        usable.append(r)
    sample = stratified_sample(usable, per_source)

    hyps = translator.translate([r[input_field] for r in sample])
    preds = [{"id": r["id"], "source": r["source"], "input": r[input_field],
              "reference": r["text_target"], "hypothesis": h} for r, h in zip(sample, hyps)]

    per = defaultdict(list)
    for p in preds:
        per[p["source"]].append(p)
    by_source = {}
    for name, rows in sorted(per.items()):
        h, ref = [p["hypothesis"] for p in rows], [p["reference"] for p in rows]
        by_source[name] = {"n": len(rows), **score(h, ref), **bootstrap_ci(h, ref, bootstrap)}

    all_h, all_r = [p["hypothesis"] for p in preds], [p["reference"] for p in preds]
    metrics = {"input_field": input_field, "per_source_limit": per_source,
               "skipped_without_input_or_reference": dict(skipped),
               "overall": {"n": len(preds), **(score(all_h, all_r) if preds else {})},
               "macro_average": ({"bleu": mean(v["bleu"] for v in by_source.values()),
                                  "chrf": mean(v["chrf"] for v in by_source.values())} if by_source else {}),
               "by_source": by_source}
    return preds, metrics
