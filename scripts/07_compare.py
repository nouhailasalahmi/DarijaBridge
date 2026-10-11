"""Paired comparison of two runs of 06_baseline.py on the SAME sentences.

  python scripts/07_compare.py val_norm val_ref                 # names = folders in data/baselines
  python scripts/07_compare.py val_norm val_ref --source doda   # one source only
"""
import argparse
from pathlib import Path

from darijabridge.evaluation.metrics import paired_bootstrap
from darijabridge.utils.io import read_jsonl


def load(base: Path, name: str, source: str | None) -> dict[str, dict]:
    rows = read_jsonl(base / name / "predictions.jsonl")
    return {r["id"]: r for r in rows if source is None or r["source"] == source}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--source")
    ap.add_argument("--base", default="data/baselines")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--report-dir", default="reports")
    args = ap.parse_args()

    base = Path(args.base)
    ra, rb = load(base, args.a, args.source), load(base, args.b, args.source)
    ids = sorted(set(ra) & set(rb))
    if len(ids) < 2:
        raise SystemExit(f"Only {len(ids)} sentences in common: the two runs must use the same sentences.")
    refs = [ra[i]["reference"] for i in ids]
    res = paired_bootstrap([ra[i]["hypothesis"] for i in ids], [rb[i]["hypothesis"] for i in ids], refs, args.n)

    L = [f"# Comparaison : {args.a} (A) contre {args.b} (B)", "",
         f"- Phrases communes : {len(ids)} (A : {len(ra)}, B : {len(rb)})"
         + (f", source : {args.source}" if args.source else ""),
         f"- Rééchantillonnages appariés : {args.n}", "",
         "| Métrique | A | B | Écart (B moins A) | IC 95 % de l'écart | B meilleur dans |", "|---|---|---|---|---|---|"]
    for m in ("chrf", "bleu"):
        r = res[m]
        L.append(f"| {m} | {r['a']:.1f} | {r['b']:.1f} | {r['delta']:+.1f} | "
                 f"[{r['ci'][0]:+.1f} ; {r['ci'][1]:+.1f}] | {100 * r['p_b_better']:.0f} % des tirages |")
    c = res["chrf"]["ci"]
    verdict = ("L'écart de chrF est probablement réel (l'intervalle ne contient pas 0)."
               if c[0] > 0 or c[1] < 0 else
               "L'intervalle de l'écart contient 0 : rien ne permet de conclure à une différence.")
    L += ["", verdict]
    Path(args.report_dir).mkdir(parents=True, exist_ok=True)
    out = Path(args.report_dir) / f"compare_{args.a}_vs_{args.b}{'_' + args.source if args.source else ''}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\nReport: {out}")


if __name__ == "__main__":
    main()
