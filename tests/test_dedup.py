from darijabridge.dataset.dedup import darija_text, deduplicate, group_id, relaxed_key


def rec(i, norm, target=None, ref=None):
    r = {"id": i, "text_darija": norm, "text_darija_norm": norm, "text_target": target}
    if ref:
        r["text_darija_ar_ref"] = ref
    return r


def test_relaxed_key_ignores_case_spaces_punctuation():
    assert relaxed_key("Salam,  ça va ?") == relaxed_key("salam ça va")
    assert relaxed_key("\u0643\u0646\u062f\u064a\u0631 !") == relaxed_key("\u0643\u0646\u062f\u064a\u0631")


def test_reference_is_preferred_for_matching():
    assert darija_text(rec("a", "predicted", ref="reference")) == "reference"
    assert darija_text(rec("b", "predicted")) == "predicted"


def test_duplicates_in_and_across_sources_first_source_wins():
    a = [rec("1", "salam", "hello"), rec("2", "Salam !", "Hello"), rec("3", "fin", "where")]
    b = [rec("4", "salam", "hello"), rec("5", "salam", "hi")]
    kept, rejected, stats = deduplicate({"a": a, "b": b})
    assert [r["id"] for r in kept] == ["1", "3", "5"]
    reasons = {r["id"]: r["reason"] for r in rejected}
    assert reasons == {"2": "duplicate_in_source", "4": "duplicate_other_source"}
    assert stats["shared_darija_between_sources"] == {"a / b": 1}


def test_same_darija_different_translations_share_a_group():
    kept, _, stats = deduplicate({"a": [rec("1", "salam", "hello"), rec("2", "salam", "hi")]})
    assert len(kept) == 2 and kept[0]["group_id"] == kept[1]["group_id"] == group_id("salam")
    assert stats["groups"] == 1 and stats["groups_with_several_records"] == 1


def test_empty_after_normalization_is_rejected():
    kept, rejected, _ = deduplicate({"a": [rec("1", "!!! ...", "x")]})
    assert not kept and rejected[0]["reason"] == "empty_after_normalization"
