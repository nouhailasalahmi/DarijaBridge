import re
from pathlib import Path
from typing import Iterator

from darijabridge.collection.base import BaseCollector, Record

TIME_RE = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->")
TAG_RE = re.compile(r"<[^>]+>|\{\\[^}]*\}|[♪♫]")


def _read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "cp1256", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, f"cannot decode {path}")


def parse_srt(text: str) -> list[tuple[float, str]]:
    """Return [(start_seconds, cleaned_text), ...]."""
    cues = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n")):
        lines = block.strip().split("\n")
        for i, line in enumerate(lines):
            m = TIME_RE.search(line)
            if m:
                h, mi, s, ms = (int(x) for x in m.groups())
                start = h * 3600 + mi * 60 + s + ms / 1000
                body = " ".join(TAG_RE.sub("", l).strip() for l in lines[i + 1:])
                body = re.sub(r"\s+", " ", body).strip()
                if body:
                    cues.append((start, body))
                break
    return cues


class SubtitlesCollector(BaseCollector):
    """.srt files in `dir`. Optional `pair_dir`: same-named .srt in another language,
    aligned by nearest start time (within `tolerance` seconds)."""

    def iter_records(self) -> Iterator[Record]:
        c = self.cfg
        tol = c.get("tolerance", 1.0)
        pair_dir = Path(c["pair_dir"]) if c.get("pair_dir") else None
        files = sorted(Path(c["dir"]).glob("*.srt"))
        if not files:
            raise FileNotFoundError(f"[{self.name}] no .srt files in {c['dir']}")
        for f in files:
            cues = parse_srt(_read_text(f))
            target_cues = []
            if pair_dir and (pair_dir / f.name).exists():
                target_cues = parse_srt(_read_text(pair_dir / f.name))
            for start, text in cues:
                target = None
                if target_cues:
                    t_start, t_text = min(target_cues, key=lambda x: abs(x[0] - start))
                    if abs(t_start - start) <= tol:
                        target = t_text
                yield Record(
                    source=self.name,
                    text_darija=text,
                    text_target=target,
                    target_lang=c.get("target_lang") if target else None,
                    license=c.get("license"),
                    meta={"file": f.name, "start": round(start, 2)},
                )
