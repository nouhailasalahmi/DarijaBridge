"""BLEU and chrF with sacreBLEU, plus a bootstrap confidence interval.

BLEU counts n-grams up to 4: a sentence shorter than 4 words cannot score on its own, so on a corpus
of short sentences chrF (character level) is the more reliable of the two.

A score without an interval is hard to interpret: on a few hundred sentences, a gap of one or two
points between two systems can be pure chance."""
import random

from sacrebleu.metrics import BLEU, CHRF


def score(hyps: list[str], refs: list[str]) -> dict:
    return {"bleu": BLEU().corpus_score(hyps, [refs]).score,
            "chrf": CHRF().corpus_score(hyps, [refs]).score}


def bootstrap_ci(hyps: list[str], refs: list[str], n: int = 200, seed: int = 0, alpha: float = 0.05) -> dict:
    """Percentile bootstrap: resample the sentences with replacement and recompute the scores."""
    if n <= 0 or len(hyps) < 2:
        return {}
    rng = random.Random(seed)
    idx = range(len(hyps))
    bleus, chrfs = [], []
    for _ in range(n):
        pick = [rng.choice(idx) for _ in idx]
        s = score([hyps[i] for i in pick], [refs[i] for i in pick])
        bleus.append(s["bleu"])
        chrfs.append(s["chrf"])
    lo, hi = int(n * alpha / 2), min(n - 1, int(n * (1 - alpha / 2)))
    bleus.sort(); chrfs.sort()
    return {"bleu_ci": (bleus[lo], bleus[hi]), "chrf_ci": (chrfs[lo], chrfs[hi])}


def signatures() -> dict:
    """Exact metric configuration, to be stored with the results (reproducibility)."""
    out = {}
    for name, metric in (("bleu", BLEU()), ("chrf", CHRF())):
        metric.corpus_score(["a"], [["a"]])          # sacreBLEU only knows its signature after a first call
        out[name] = str(metric.get_signature())
    return out


def paired_bootstrap(hyps_a: list[str], hyps_b: list[str], refs: list[str], n: int = 1000,
                     seed: int = 0, alpha: float = 0.05) -> dict:
    """Compares two systems translating the SAME sentences. Each resample picks sentences and scores
    both systems on them, so the interval is on the DIFFERENCE (b - a) and is much tighter than
    comparing two separate intervals. `p_b_better` = share of resamples where b beats a."""
    rng = random.Random(seed)
    idx = range(len(refs))
    deltas = {"bleu": [], "chrf": []}
    for _ in range(n):
        pick = [rng.choice(idx) for _ in idx]
        r = [refs[i] for i in pick]
        sa = score([hyps_a[i] for i in pick], r)
        sb = score([hyps_b[i] for i in pick], r)
        for m in deltas:
            deltas[m].append(sb[m] - sa[m])
    full_a, full_b = score(hyps_a, refs), score(hyps_b, refs)
    out = {}
    lo, hi = int(n * alpha / 2), min(n - 1, int(n * (1 - alpha / 2)))
    for m, d in deltas.items():
        d.sort()
        out[m] = {"a": full_a[m], "b": full_b[m], "delta": full_b[m] - full_a[m],
                  "ci": (d[lo], d[hi]), "p_b_better": sum(x > 0 for x in d) / n}
    return out
