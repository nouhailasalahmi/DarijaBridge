import csv
import json
from pathlib import Path
from typing import Iterator

from darijabridge.collection.base import BaseCollector, Record
from darijabridge.utils.io import download_file


class TabularCollector(BaseCollector):
    """CSV / TSV / JSONL files with a configurable column mapping.

    Config keys:
      path | url        local file, or URL to download into data/raw/<name>/
      format            csv | tsv | jsonl (default: guessed from extension)
      header            true/false (default true). If false, give `columns: [...]`
      columns           column names when the file has no header
      darija_col        column holding the Darija text
      target_col        column holding the translation (optional)
      target_lang       e.g. "fr", "en", "ar"
      filter            {column: ..., values: [...]} keep only matching rows
      license           license string stored in every record
      meta_cols         extra columns to keep in `meta`
      pair_path         optional second file (same layout) holding the translation,
                        joined on `id_col` (e.g. MADAR city file + MADAR MSA file)
      id_col            column used for the join
      pair_text_col     text column of the pair file (default: darija_col)
    """

    def _resolve_input(self) -> Path:
        if self.cfg.get("path"):
            p = Path(self.cfg["path"])
            if not p.exists():
                raise FileNotFoundError(f"[{self.name}] file not found: {p}")
            return p
        if self.cfg.get("url"):
            dest = self.out_dir / "download" / Path(self.cfg["url"]).name
            if not dest.exists():
                self.log.info("downloading %s", self.cfg["url"])
                download_file(self.cfg["url"], dest)
            return dest
        raise ValueError(f"[{self.name}] config needs `path` or `url`")

    def _rows(self, path: Path) -> Iterator[dict]:
        fmt = self.cfg.get("format") or path.suffix.lstrip(".").lower()
        if fmt == "jsonl":
            with path.open(encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        yield json.loads(line)
            return
        delimiter = "\t" if fmt == "tsv" else ","
        # TSV files (e.g. MADAR) can contain stray quote characters in sentences: do not parse quotes
        quoting = csv.QUOTE_NONE if fmt == "tsv" else csv.QUOTE_MINIMAL
        with path.open(encoding="utf-8-sig", newline="") as f:
            if self.cfg.get("header", True):
                reader = csv.DictReader(f, delimiter=delimiter, quoting=quoting)
            else:
                reader = csv.DictReader(f, delimiter=delimiter, quoting=quoting,
                                        fieldnames=self.cfg["columns"])
            yield from reader

    def _load_pairs(self) -> dict[str, str] | None:
        c = self.cfg
        if not c.get("pair_path"):
            return None
        pair = Path(c["pair_path"])
        if not pair.exists():
            raise FileNotFoundError(f"[{self.name}] pair file not found: {pair}")
        text_col = c.get("pair_text_col", c["darija_col"])
        pairs: dict[str, str] = {}
        for row in self._rows(pair):
            key, text = row.get(c["id_col"]), (row.get(text_col) or "").strip()
            if key and text and key not in pairs:
                pairs[key] = text
        return pairs

    def iter_records(self) -> Iterator[Record]:
        c = self.cfg
        flt = c.get("filter")
        pairs = self._load_pairs()
        yield from self._iter(c, flt, pairs)

    def _iter(self, c, flt, pairs) -> Iterator[Record]:
        n_total = n_paired = 0
        for row in self._rows(self._resolve_input()):
            if flt and row.get(flt["column"]) not in flt["values"]:
                continue
            darija = (row.get(c["darija_col"]) or "").strip()
            if not darija:
                continue
            if pairs is not None:
                target = pairs.get(row.get(c["id_col"]))
                n_total += 1
                n_paired += target is not None
            else:
                target = (row.get(c["target_col"]) or "").strip() if c.get("target_col") else None
            yield Record(
                source=self.name,
                text_darija=darija,
                text_target=target or None,
                target_lang=c.get("target_lang") if target else None,
                license=c.get("license"),
                meta={k: row.get(k) for k in c.get("meta_cols", [])},
            )
        if pairs is not None:
            self.log.info("%d / %d records matched a translation by %s", n_paired, n_total, c["id_col"])


class DodaCollector(TabularCollector):
    """DODA (Darija Open Dataset). Point `path`/`url` to the file you downloaded
    and set the column names to match it."""


class MadarCollector(TabularCollector):
    """MADAR parallel corpus. Access requires a license request to the authors;
    download it manually, set `path`, and use `filter` to keep Moroccan cities."""