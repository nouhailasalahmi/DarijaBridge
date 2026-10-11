"""Deduplication on the NORMALIZED text, across all sources.

Why after normalization: the same sentence can be written in Arabizi in one source and in
Arabic script in another, or with different spellings/punctuation. Only the normalized form
makes them comparable.

Two outputs:
  - exact duplicates of a (darija, translation) pair are removed (first source in the list wins)
  - every kept record gets a `group_id` = hash of its Darija text. Records that share the same
    Darija (e.g. several translations of one sentence) share a group, and the train/validation/
    test split must keep a whole group on one side, otherwise the test set leaks into training.
"""
import hashlib
import re
from collections import Counter, defaultdict
from itertools import combinations
from typing import Iterable

_NON_LETTERS = re.compile(r"[\W_]+")


def relaxed_key(text: str) -> str:
    """Lower-cased text without spaces or punctuation: 'Salam, ça va ?' ~ 'salam ça va'."""
    return _NON_LETTERS.sub("", text.casefold())


def darija_text(rec: dict) -> str:
    """Best Arabic-script form of the Darija: the reference when the source gives one (DODA),
    otherwise the prediction of the normalizer."""
    return rec.get("text_darija_ar_ref") or rec.get("text_darija_norm") or rec["text_darija"]


def group_id(darija_key: str) -> str:
    return hashlib.sha1(darija_key.encode("utf-8")).hexdigest()[:12]


def deduplicate(sources: dict[str, Iterable[dict]]) -> tuple[list[dict], list[dict], dict]:
    """`sources` is ordered: the first source keeps a sentence that appears in several.
    Returns (kept_records, rejected_records, stats)."""
    first_seen: dict[tuple[str, str], str] = {}          # (darija_key, target_key) -> source
    sources_of_key: dict[str, set[str]] = defaultdict(set)
    kept, rejected = [], []
    per_source = {name: {"read": 0, "kept": 0, "rejected": Counter()} for name in sources}

    for name, records in sources.items():
        s = per_source[name]
        for rec in records:
            s["read"] += 1
            dk = relaxed_key(darija_text(rec))
            reason = None
            if not dk:
                reason = "empty_after_normalization"
            else:
                sources_of_key[dk].add(name)
                tk = relaxed_key(rec["text_target"]) if rec.get("text_target") else ""
                owner = first_seen.get((dk, tk))
                if owner is None:
                    first_seen[(dk, tk)] = name
                else:
                    reason = "duplicate_in_source" if owner == name else "duplicate_other_source"
            if reason:
                s["rejected"][reason] += 1
                rejected.append({"id": rec["id"], "source": name, "reason": reason,
                                 "text_darija": rec["text_darija"], "text_target": rec.get("text_target")})
            else:
                s["kept"] += 1
                kept.append(dict(rec, group_id=group_id(dk)))
    return kept, rejected, _summarize(per_source, kept, sources_of_key)


def _summarize(per_source: dict, kept: list[dict], sources_of_key: dict[str, set[str]]) -> dict:
    sizes = Counter(r["group_id"] for r in kept)
    overlap: Counter = Counter()
    for srcs in sources_of_key.values():
        for a, b in combinations(sorted(srcs), 2):
            overlap[f"{a} / {b}"] += 1
    return {
        "sources": {n: {"read": s["read"], "kept": s["kept"], "rejected": dict(s["rejected"])}
                    for n, s in per_source.items()},
        "kept": len(kept),
        "groups": len(sizes),
        "groups_with_several_records": sum(1 for v in sizes.values() if v > 1),
        "largest_group": max(sizes.values()) if sizes else 0,
        "shared_darija_between_sources": dict(overlap),
    }
