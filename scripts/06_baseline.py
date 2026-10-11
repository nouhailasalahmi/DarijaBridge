"""Zero-shot baseline: NLLB without any training, scored on the test split.

  python scripts/06_baseline.py                                   # uses configs/baseline.yaml
  python scripts/06_baseline.py --input-field text_darija         # another input (ablation)
  python scripts/06_baseline.py --dry-run                         # no model: checks the pipeline
  python scripts/06_baseline.py --per-source 50                   # quick trial
"""
import argparse
import json
import platform
from pathlib import Path

import yaml

from darijabridge.evaluation.metrics import signatures
from darijabridge.evaluation.runner import run_baseline
from darijabridge.models.nllb import IdentityTranslator
from darijabridge.utils.io import read_jsonl
from darijabridge.utils.logging import get_logger

log = get_logger("baseline")


def versions() -> dict:
    out = {"python": platform.python_version()}
    for pkg in ("torch", "transformers", "sacrebleu"):
        try:
            out[pkg] = __import__(pkg).__version__
        except ImportError:
            out[pkg] = None
    return out


def write_report(path: Path, name: str, cfg: dict, m: dict) -> None:
    L = [f"# Baseline : {name}", "",
         f"- Modèle : `{cfg['model']}` ({cfg['src_lang']} vers {cfg['tgt_lang']}), "
         f"{cfg['num_beams']} faisceaux, découpage `{cfg['split']}`",
         f"- Entrée donnée au modèle : `{m['input_field']}`",
         f"- Phrases évaluées : {m['overall']['n']} (au plus {m['per_source_limit']} par source)", ""]
    if m["skipped_without_input_or_reference"]:
        L += [f"- Ignorées (champ d'entrée ou référence absents) : {m['skipped_without_input_or_reference']}", ""]
    L += ["| Source | n | BLEU | chrF | chrF IC 95 % |", "|---|---|---|---|---|"]
    for s, v in m["by_source"].items():
        ci = v.get("chrf_ci")
        warn = " (n faible)" if v["n"] < 30 else ""
        L.append(f"| {s}{warn} | {v['n']} | {v['bleu']:.1f} | {v['chrf']:.1f} | "
                 + (f"[{ci[0]:.1f} ; {ci[1]:.1f}]" if ci else "-") + " |")
    if m["macro_average"]:
        L.append(f"| **Moyenne des sources** | | {m['macro_average']['bleu']:.1f} | {m['macro_average']['chrf']:.1f} | |")
    L.append(f"| Toutes phrases confondues | {m['overall']['n']} | {m['overall'].get('bleu', 0):.1f} | "
             f"{m['overall'].get('chrf', 0):.1f} | |")
    L += ["", "Les scores par source sont à privilégier : DODA domine le jeu de test.",
          "", f"Signatures sacreBLEU : `{m['signatures']['bleu']}` ; `{m['signatures']['chrf']}`"]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/baseline.yaml")
    ap.add_argument("--input-field")
    ap.add_argument("--per-source", type=int)
    ap.add_argument("--split")
    ap.add_argument("--name")
    ap.add_argument("--split-dir", help="folder with train/validation/test.jsonl (e.g. on Kaggle)")
    ap.add_argument("--model", help="model name or local folder, e.g. models/nllb600m_ft_norm/best")
    ap.add_argument("--sources", nargs="*", help="only these sources, e.g. --sources doda")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    for key, val in (("input_field", args.input_field), ("per_source", args.per_source), ("split", args.split)):
        if val is not None:
            cfg[key] = val
    if args.sources:
        cfg["sources"] = args.sources
    if args.model:
        cfg["model"] = args.model
    if args.split_dir:
        cfg["split_dir"] = args.split_dir
    name = args.name or f"{'dryrun' if args.dry_run else 'nllb'}_{cfg['split']}_{cfg['input_field']}"

    if args.dry_run:
        translator = IdentityTranslator()
    else:
        from darijabridge.models.nllb import NllbTranslator
        translator = NllbTranslator(cfg["model"], cfg["src_lang"], cfg["tgt_lang"],
                                    cfg["num_beams"], cfg["max_length"], cfg["batch_size"])

    records = list(read_jsonl(Path(cfg["split_dir"]) / f"{cfg['split']}.jsonl"))
    preds, metrics = run_baseline(records, translator, cfg["input_field"], cfg.get("per_source"),
                                  cfg.get("bootstrap", 0), cfg.get("sources"))
    metrics.update(signatures=signatures(), config=cfg, versions=versions(), name=name)

    out_dir = Path(cfg["output_dir"]) / name
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "predictions.jsonl").open("w", encoding="utf-8") as f:
        for p in preds:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    report_dir = Path(cfg["report_dir"])
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / f"baseline_{name}.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(report_dir / f"baseline_{name}.md", name, cfg, metrics)

    print(f"\n=== {name} ===")
    for s, v in metrics["by_source"].items():
        print(f"{s:20} n={v['n']:>4} BLEU={v['bleu']:5.1f} chrF={v['chrf']:5.1f}")
    print(f"\nReport: {report_dir}/baseline_{name}.md   Predictions: {out_dir}/predictions.jsonl")


if __name__ == "__main__":
    main()
