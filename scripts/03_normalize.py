"""Usage: python scripts/03_normalize.py [--config configs/normalization.yaml] [--skip-eval]

1. learns an Arabizi -> Arabic lexicon from the DODA train part and evaluates on the held-out part
2. adds `text_darija_norm` to every record of data/interim/ and writes data/processed/
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import yaml

from darijabridge.normalization.arabizi import Transliterator
from darijabridge.normalization.evaluate import evaluate, is_test
from darijabridge.normalization.lexicon import build_lexicon, save_lexicon
from darijabridge.normalization.pipeline import Normalizer
from darijabridge.utils.io import read_jsonl
from darijabridge.utils.logging import get_logger

log = get_logger("normalization")


def learn_and_evaluate(cfg: dict, skip_eval: bool) -> tuple[dict, dict]:
    lc = cfg["lexicon"]
    path = Path(cfg["input_dir"]) / f"{lc['source']}.jsonl"
    train, test = [], []
    for rec in read_jsonl(path):
        gold = (rec.get("meta") or {}).get(lc["gold_field"])
        if gold:
            (test if is_test(rec["id"], lc["test_mod"]) else train).append((rec["text_darija"], gold))
    lexicon = build_lexicon(train, lc.get("min_count", 1))
    save_lexicon(lexicon, cfg["lexicon_path"],
                 {"source": lc["source"], "train_sentences": len(train), "heldout_sentences": len(test)})
    log.info("lexicon: %d words from %d sentences (%d held out)", len(lexicon), len(train), len(test))

    results = {"train_sentences": len(train), "heldout_sentences": len(test), "lexicon_size": len(lexicon)}
    if not skip_eval:
        results["rules_only"] = evaluate(Transliterator({}, cfg.get("arabic_punct", True)), test)
        results["lexicon_plus_rules"] = evaluate(Transliterator(lexicon, cfg.get("arabic_punct", True)), test)
    return results, lexicon


def write_report(cfg: dict, results: dict, stats: dict) -> None:
    report_dir = Path(cfg["report_dir"])
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "normalization_report.json").write_text(
        json.dumps({"transliteration": results, "sources": stats}, ensure_ascii=False, indent=2), encoding="utf-8")
    L = ["# Rapport de normalisation", "", "## Translittération Arabizi vers arabe (jeu de test DODA mis de côté)", ""]
    L += [f"Lexique appris sur {results['train_sentences']} phrases ({results['lexicon_size']} mots), "
          f"évalué sur {results['heldout_sentences']} phrases mises de côté.", ""]
    if "rules_only" in results:
        L += ["| Méthode | Mots corrects | CER | Phrases exactes | Mots inconnus du lexique | Exactitude sur mots inconnus |",
              "|---|---|---|---|---|---|"]
        for name, key in [("Règles seules", "rules_only"), ("Lexique + règles", "lexicon_plus_rules")]:
            r = results[key]
            if key == "rules_only":
                oov_rate, oov = "-", "-"
            else:
                oov_rate = f"{100 * r['oov_rate']:.1f} %"
                oov = f"{100 * r['oov_word_accuracy']:.1f} %" if r["oov_word_accuracy"] is not None else "-"
            L.append(f"| {name} | {100 * r['word_accuracy']:.1f} % | {100 * r['cer']:.1f} % | "
                     f"{100 * r['sentence_exact']:.1f} % | {oov_rate} | {oov} |")
        L.append("")
    L += ["## Répartition des écritures par source", "", "| Source | Enregistrements | arabic | latin | mixed | none | Mots latins hors lexique (moyenne) | Avec arabe de référence | Dont identique à la prédiction |",
          "|---|---|---|---|---|---|---|---|---|"]
    for name, s in stats.items():
        sc = s["scripts"]
        L.append(f"| {name} | {s['records']} | {sc.get('arabic', 0)} | {sc.get('latin', 0)} | "
                 f"{sc.get('mixed', 0)} | {sc.get('none', 0)} | "
                 f"{'-' if s['mean_unknown_ratio'] is None else format(100 * s['mean_unknown_ratio'], '.1f') + ' %'} | "
                 f"{s['with_reference']} | {s['reference_identical_to_prediction']} |")
    (report_dir / "normalization_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/normalization.yaml")
    parser.add_argument("--skip-eval", action="store_true")
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    results, lexicon = learn_and_evaluate(cfg, args.skip_eval)
    norm = Normalizer(lexicon, cfg.get("arabic_punct", True), cfg.get("unify_gaf", True),
                      cfg.get("reference_field"))
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = {}
    for source in cfg["sources"]:
        src = Path(cfg["input_dir"]) / f"{source}.jsonl"
        if not src.exists():
            log.warning("skip %s: %s not found", source, src)
            continue
        scripts, n, unk_sum, unk_n, with_ref, same = Counter(), 0, 0.0, 0, 0, 0
        with (out_dir / f"{source}.jsonl").open("w", encoding="utf-8") as f:
            for rec in read_jsonl(src):
                out = norm.normalize_record(rec)
                scripts[out["meta"]["script"]] += 1
                n += 1
                if "text_darija_ar_ref" in out:
                    with_ref += 1
                    same += out["text_darija_ar_ref"] == out["text_darija_norm"]
                if "translit_unknown_ratio" in out["meta"]:
                    unk_sum += out["meta"]["translit_unknown_ratio"]
                    unk_n += 1
                f.write(json.dumps(out, ensure_ascii=False) + "\n")
        stats[source] = {"records": n, "scripts": dict(scripts),
                         "mean_unknown_ratio": round(unk_sum / unk_n, 3) if unk_n else None,
                         "with_reference": with_ref, "reference_identical_to_prediction": same}
        log.info("%s: %d records, scripts=%s", source, n, dict(scripts))

    write_report(cfg, results, stats)
    print("\n=== Normalization summary ===")
    if "rules_only" in results:
        for key in ("rules_only", "lexicon_plus_rules"):
            r = results[key]
            print(f"{key:20} word_acc={r['word_accuracy']:.3f} CER={r['cer']:.3f} sentence_exact={r['sentence_exact']:.3f}")
    print(f"\nReport: {cfg['report_dir']}/normalization_report.md")


if __name__ == "__main__":
    main()
