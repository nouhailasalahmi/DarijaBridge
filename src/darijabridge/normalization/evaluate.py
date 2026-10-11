"""Evaluation of the transliteration against gold Arabic-script text."""
import hashlib
import re

from darijabridge.normalization.arabizi import Transliterator
from darijabridge.normalization.orthography import normalize_arabic

_TOKEN = re.compile(r"[^\W_]+")


def is_test(record_id: str, mod: int = 10) -> bool:
    """Deterministic split on the record id: about 1/mod of the records are held out."""
    return int(hashlib.sha1(record_id.encode("utf-8")).hexdigest()[:8], 16) % mod == 0


def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def evaluate(translit: Transliterator, pairs: list[tuple[str, str]]) -> dict:
    """pairs = (latin_sentence, gold_arabic_sentence). Only sentences with the same number of
    words on both sides are scored (word-by-word comparison needs that alignment)."""
    words = ok = oov = oov_ok = chars = errors = sent = sent_ok = 0
    for latin, gold in pairs:
        wl, wg = _TOKEN.findall(latin.lower()), _TOKEN.findall(normalize_arabic(gold))
        if not wl or len(wl) != len(wg):
            continue
        sent += 1
        all_ok = True
        for x, y in zip(wl, wg):
            pred, known = translit.word(x)
            words += 1
            chars += len(y)
            errors += edit_distance(pred, y)
            hit = pred == y
            ok += hit
            all_ok &= hit
            if not known:
                oov += 1
                oov_ok += hit
        sent_ok += all_ok
    return {"sentences": sent, "words": words,
            "word_accuracy": ok / words, "cer": errors / chars, "sentence_exact": sent_ok / sent,
            "oov_rate": oov / words, "oov_word_accuracy": oov_ok / oov if oov else None}
