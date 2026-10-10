from pathlib import Path
from typing import Iterator

from darijabridge.collection.base import BaseCollector, Record


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8-sig").splitlines()


class PlainTextCollector(BaseCollector):
    """Plain-text files, one sentence per line (e.g. the MADAR city files).

    Config keys:
      path        file with the Darija sentences
      pair_path   optional file whose line i is the translation of line i of `path`
      target_lang language of pair_path (e.g. "ar" for MSA)
      meta        dict copied into every record (e.g. {city: Rabat})
      license     license string stored in every record
    """

    def iter_records(self) -> Iterator[Record]:
        c = self.cfg
        path = Path(c["path"])
        if not path.exists():
            raise FileNotFoundError(f"[{self.name}] file not found: {path}")
        darija_lines = _read_lines(path)

        target_lines = None
        if c.get("pair_path"):
            pair = Path(c["pair_path"])
            if not pair.exists():
                raise FileNotFoundError(f"[{self.name}] file not found: {pair}")
            target_lines = _read_lines(pair)
            if len(target_lines) != len(darija_lines):
                raise ValueError(
                    f"[{self.name}] line counts differ ({len(darija_lines)} vs "
                    f"{len(target_lines)}): files are not line-aligned, check them before use"
                )

        for i, line in enumerate(darija_lines):
            text = line.strip()
            if not text:
                continue
            target = target_lines[i].strip() if target_lines else None
            yield Record(
                source=self.name,
                text_darija=text,
                text_target=target or None,
                target_lang=c.get("target_lang") if target else None,
                license=c.get("license"),
                meta={**c.get("meta", {}), "line": i + 1},
            )