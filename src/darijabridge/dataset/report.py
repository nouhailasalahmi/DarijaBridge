import json
from pathlib import Path


def write_dedup_report(summary: dict, report_dir: str | Path) -> Path:
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "dedup_report.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    srcs = summary["sources"]
    L = ["# Rapport de déduplication", "", "## Bilan par source", "",
         "| Source | Lus | Gardés | Rejetés | Taux de rejet |", "|---|---|---|---|---|"]
    read = kept = 0
    for name, s in srcs.items():
        rej = s["read"] - s["kept"]
        read += s["read"]; kept += s["kept"]
        L.append(f"| {name} | {s['read']} | {s['kept']} | {rej} | {100 * rej / s['read'] if s['read'] else 0:.1f} % |")
    L.append(f"| **Total** | {read} | {kept} | {read - kept} | {100 * (read - kept) / read if read else 0:.1f} % |")

    reasons = sorted({r for s in srcs.values() for r in s["rejected"]})
    if reasons:
        L += ["", "## Rejets par raison", "", "| Raison | " + " | ".join(srcs) + " |", "|---|" + "---|" * len(srcs)]
        for r in reasons:
            L.append(f"| {r} | " + " | ".join(str(s["rejected"].get(r, 0)) for s in srcs.values()) + " |")

    L += ["", "## Groupes (même texte Darija)", "",
          f"- Groupes distincts : {summary['groups']}",
          f"- Groupes avec plusieurs enregistrements (plusieurs traductions) : {summary['groups_with_several_records']}",
          f"- Plus grand groupe : {summary['largest_group']} enregistrements", ""]
    L.append("Le découpage entraînement / validation / test devra garder chaque groupe entier d'un seul côté.")

    shared = summary["shared_darija_between_sources"]
    L += ["", "## Textes Darija communs à plusieurs sources", ""]
    if shared:
        L += ["| Paire de sources | Textes Darija en commun |", "|---|---|"]
        L += [f"| {k} | {v} |" for k, v in sorted(shared.items(), key=lambda kv: -kv[1])]
    else:
        L.append("Aucun chevauchement détecté.")
    path = report_dir / "dedup_report.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


def write_split_report(summary: dict, params: dict, report_dir: str | Path) -> Path:
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "split_report.json").write_text(
        json.dumps({"params": params, **summary}, ensure_ascii=False, indent=2), encoding="utf-8")
    splits = ("train", "validation", "test")
    L = ["# Rapport de découpage", "",
         f"Découpage par groupe (hash du texte Darija) : validation {params['validation']:.0%}, "
         f"test {params['test']:.0%}, sel `{params['salt']}`.", "",
         f"- Groupes : {summary['groups']}",
         f"- **Groupes présents dans plusieurs découpages : {summary['groups_in_several_splits']}** (doit valoir 0)", ""]
    for task, sp in summary["tasks"].items():
        title = "sans traduction (Darija seul)" if task == "none" else f"Darija vers `{task}`"
        L += [f"## Tâche : {title}", "", "| Source | train | validation | test |", "|---|---|---|---|"]
        sources = sorted({s for x in splits for s in sp[x]["by_source"]})
        for s in sources:
            L.append(f"| {s} | " + " | ".join(str(sp[x]["by_source"].get(s, 0)) for x in splits) + " |")
        tot = [sp[x]["records"] for x in splits]
        n = sum(tot) or 1
        L.append("| **Total** | " + " | ".join(f"{t} ({100 * t / n:.1f} %)" for t in tot) + " |")
        if "test_target_seen_in_train" in sp:
            L += ["", f"Phrases de test dont la traduction apparaît aussi dans train : "
                      f"{sp['test_target_seen_in_train']} sur {sp['test']['records']} "
                      "(courtes réponses génériques du type « Yes. », sans fuite du Darija)."]
        L.append("")
    path = report_dir / "split_report.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
