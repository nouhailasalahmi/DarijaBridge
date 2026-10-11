from darijabridge.dataset.split import assign, split_of, summarize


def recs(n, source="a", tl="en", start=0):
    return [{"id": str(i), "group_id": f"g{i}", "source": source, "target_lang": tl,
             "text_target": f"t{i}"} for i in range(start, start + n)]


def test_deterministic_and_proportions():
    assert split_of("g1") == split_of("g1")
    counts = {"train": 0, "validation": 0, "test": 0}
    for i in range(20000):
        counts[split_of(f"g{i}")] += 1
    assert abs(counts["test"] / 20000 - 0.10) < 0.01 and abs(counts["validation"] / 20000 - 0.10) < 0.01


def test_same_group_same_split_even_across_sources_and_targets():
    rows = recs(1, "a", "en") + recs(1, "b", None) + recs(1, "c", "fr")      # all share group g0
    by_task = assign(rows)
    assert summarize(by_task)["groups_in_several_splits"] == 0
    found = {s for t in by_task.values() for s, v in t.items() if v}
    assert len(found) == 1


def test_adding_data_never_moves_existing_records():
    before = {r["id"]: s for t in assign(recs(500)).values() for s, v in t.items() for r in v}
    after = {r["id"]: s for t in assign(recs(500) + recs(500, "b", "fr", start=500)).values()
             for s, v in t.items() for r in v}
    assert all(after[i] == s for i, s in before.items())


def test_records_are_split_per_target_language():
    by_task = assign(recs(50, tl="en") + recs(50, tl=None, start=50))
    assert set(by_task) == {"en", "none"}
