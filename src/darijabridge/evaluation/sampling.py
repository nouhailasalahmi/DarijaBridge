import hashlib
from collections import defaultdict


def stratified_sample(records: list[dict], per_source: int | None) -> list[dict]:
    """At most `per_source` records from each source, chosen by a hash of the id (so the sample is
    the same on every run and on every machine). None = keep everything."""
    by_source: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_source[r["source"]].append(r)
    out = []
    for name in sorted(by_source):
        rows = sorted(by_source[name], key=lambda r: hashlib.sha1(r["id"].encode("utf-8")).hexdigest())
        out += rows if per_source is None else rows[:per_source]
    return out
