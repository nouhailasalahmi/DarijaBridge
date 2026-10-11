from darijabridge.evaluation.metrics import bootstrap_ci, score
from darijabridge.evaluation.runner import run_baseline
from darijabridge.evaluation.sampling import stratified_sample
from darijabridge.models.nllb import IdentityTranslator


def rec(i, source, src_text, ref, **extra):
    return {"id": str(i), "source": source, "text_darija_norm": src_text, "text_target": ref, **extra}


def test_perfect_translation_scores_100():
    text = "the quick brown fox jumps over the lazy dog"
    s = score([text], [text])
    assert abs(s["bleu"] - 100) < 1e-6 and abs(s["chrf"] - 100) < 1e-6


def test_bootstrap_interval_contains_the_score():
    hyps = [f"sentence number {i} is here" for i in range(40)]
    refs = [f"sentence number {i} is there" if i % 3 == 0 else h for i, h in enumerate(hyps)]
    s, ci = score(hyps, refs), bootstrap_ci(hyps, refs, n=50)
    assert ci["chrf_ci"][0] <= s["chrf"] <= ci["chrf_ci"][1]
    assert bootstrap_ci(hyps, refs, n=0) == {}


def test_stratified_sample_is_limited_and_reproducible():
    rows = [rec(i, "a" if i % 2 else "b", "x", "y") for i in range(100)]
    s1, s2 = stratified_sample(rows, 10), stratified_sample(list(reversed(rows)), 10)
    assert len(s1) == 20 and [r["id"] for r in s1] == [r["id"] for r in s2]
    assert len(stratified_sample(rows, None)) == 100


def test_runner_skips_missing_fields_and_scores_per_source():
    rows = [rec(1, "doda", "the cat sat on the mat today", "the cat sat on the mat today"),
            rec(2, "doda", "a dog ran across the wide field", "a dog ran across the wide field"),
            rec(3, "web", "no ref here", None), rec(4, "web", "", "empty input")]
    preds, m = run_baseline(rows, IdentityTranslator(), "text_darija_norm", bootstrap=0)
    assert len(preds) == 2 and set(m["by_source"]) == {"doda"}
    assert m["skipped_without_input_or_reference"] == {"web": 2}
    assert abs(m["by_source"]["doda"]["bleu"] - 100) < 1e-6


def test_input_field_ablation_uses_the_requested_field():
    rows = [rec(1, "doda", "pred", "ref", text_darija_ar_ref="reference text")]
    preds, _ = run_baseline(rows, IdentityTranslator(), "text_darija_ar_ref", bootstrap=0)
    assert preds[0]["input"] == "reference text"
