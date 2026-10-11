from darijabridge.evaluation.metrics import paired_bootstrap

REFS = [f"the quick brown fox number {i} jumps over the lazy dog" for i in range(60)]


def test_identical_systems_have_zero_difference():
    r = paired_bootstrap(REFS[:], REFS[:], REFS, n=50)
    assert r["chrf"]["delta"] == 0 and r["chrf"]["ci"] == (0, 0)


def test_clearly_better_system_is_detected():
    bad = [f"a completely different sentence {i}" for i in range(60)]
    r = paired_bootstrap(bad, REFS[:], REFS, n=50)
    assert r["chrf"]["delta"] > 20 and r["chrf"]["ci"][0] > 0 and r["chrf"]["p_b_better"] == 1.0


def test_small_difference_interval_contains_zero():
    a = REFS[:]
    b = [h.replace("lazy", "sleepy") if i % 2 else h for i, h in enumerate(REFS)]
    c = paired_bootstrap(a, b, REFS, n=100)["chrf"]
    assert c["delta"] < 0 and c["ci"][0] < c["delta"] < c["ci"][1]