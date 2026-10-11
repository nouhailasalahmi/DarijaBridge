"""Word lexicon Arabizi -> Arabic learned from aligned sentence pairs (e.g. DODA)."""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from darijabridge.normalization.orthography import normalize_arabic

_TOKEN = re.compile(r"[^\W_]+")


def build_lexicon(pairs: Iterable[tuple[str, str]], min_count: int = 1) -> dict[str, str]:
    """pairs = (latin_sentence, arabic_sentence). Words are aligned by position, which is only
    trusted when both sides have the same number of words. The most frequent Arabic form wins."""
    counts: dict[str, Counter] = defaultdict(Counter)
    for latin, arabic in pairs:
        wl, wa = _TOKEN.findall(latin.lower()), _TOKEN.findall(normalize_arabic(arabic))
        if wl and len(wl) == len(wa):
            for x, y in zip(wl, wa):
                counts[x][y] += 1
    lexicon = {}
    for word, c in counts.items():
        form, n = c.most_common(1)[0]
        if n >= min_count:
            lexicon[word] = form
    return lexicon


def save_lexicon(lexicon: dict[str, str], path: str | Path, meta: dict | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"meta": meta or {}, "entries": lexicon}, ensure_ascii=False),
                    encoding="utf-8")


def load_lexicon(path: str | Path) -> dict[str, str]:
    return json.loads(Path(path).read_text(encoding="utf-8"))["entries"]
