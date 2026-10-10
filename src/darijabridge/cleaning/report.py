import json
from pathlib import Path


def write_report(stats: dict, report_dir: str | Path) -> Path:
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "cleaning_report.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["# Rapport de nettoyage", "", "## Bilan par source", "",
             "| Source | Lus | Gardés | Rejetés | Taux de rejet | Avec traduction |",
             "|---|---|---|---|---|---|"]
    tot_read = tot_kept = 0
    for name, s in stats.items():
        rej = s["read"] - s["kept"]
        tot_read += s["read"]; tot_kept += s["kept"]
        rate = 100 * rej / s["read"] if s["read"] else 0
        lines.append(f"| {name} | {s['read']} | {s['kept']} | {rej} | {rate:.1f} % | {s['with_target']} |")
    lines.append(f"| **Total** | {tot_read} | {tot_kept} | {tot_read - tot_kept} | "
                 f"{100 * (tot_read - tot_kept) / tot_read if tot_read else 0:.1f} % | |")

    reasons = sorted({r for s in stats.values() for r in s["rejected"]})
    if reasons:
        lines += ["", "## Rejets par raison", "", "| Raison | " + " | ".join(stats) + " |",
                  "|---|" + "---|" * len(stats)]
        for r in reasons:
            lines.append(f"| {r} | " + " | ".join(str(s["rejected"].get(r, 0)) for s in stats.values()) + " |")

    steps = sorted({r for s in stats.values() for r in s["modified"]})
    if steps:
        lines += ["", "## Enregistrements modifiés par étape", "", "| Étape | " + " | ".join(stats) + " |",
                  "|---|" + "---|" * len(stats)]
        for r in steps:
            lines.append(f"| {r} | " + " | ".join(str(s["modified"].get(r, 0)) for s in stats.values()) + " |")

    path = report_dir / "cleaning_report.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
