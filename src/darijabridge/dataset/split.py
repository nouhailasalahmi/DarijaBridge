"""Train / validation / test split, BY GROUP.

Every record carries a `group_id` (hash of its Darija text, see dedup.py). The split of a group is
a pure function of its id, a salt and the fractions:

  - all records of a group go to the same split (no leakage of one Darija sentence into the test)
  - the assignment does not depend on the other records: adding a new source, or a new target
    language (MADAR/MSA pairs, synthetic French...) later never moves an existing record
  - records are written per target language, so each translation task has its own train/val/test
"""
import hashlib
from collections import Counter, defaultdict

from darijabridge.dataset.dedup import relaxed_key

SPLITS = ("train", "validation", "test")


def split_of(group: str, validation: float = 0.1, test: float = 0.1, salt: str = "darijabridge-v1") -> str:
    h = int(hashlib.sha1(f"{salt}:{group}".encode("utf-8")).hexdigest()[:8], 16) / 16 ** 8
    if h < test:
        return "test"
    if h < test + validation:
        return "validation"
    return "train"


def assign(records, validation: float = 0.1, test: float = 0.1, salt: str = "darijabridge-v1"):
    """Returns {target_lang or 'none': {split: [records]}}."""
    out: dict[str, dict[str, list]] = defaultdict(lambda: {s: [] for s in SPLITS})
    for r in records:
        out[r.get("target_lang") or "none"][split_of(r["group_id"], validation, test, salt)].append(r)
    return out


def summarize(by_task: dict) -> dict:
    groups: dict[str, set[str]] = defaultdict(set)
    tasks = {}
    for task, splits in by_task.items():
        tasks[task] = {}
        for split, rows in splits.items():
            tasks[task][split] = {"records": len(rows), "by_source": dict(Counter(r["source"] for r in rows))}
            for r in rows:
                groups[r["group_id"]].add(split)
        if task != "none":
            train_targets = {relaxed_key(r["text_target"]) for r in splits["train"] if r.get("text_target")}
            test_rows = [r for r in splits["test"] if r.get("text_target")]
            seen = sum(1 for r in test_rows if relaxed_key(r["text_target"]) in train_targets)
            tasks[task]["test_target_seen_in_train"] = seen
    return {"tasks": tasks,
            "groups": len(groups),
            "groups_in_several_splits": sum(1 for s in groups.values() if len(s) > 1)}
