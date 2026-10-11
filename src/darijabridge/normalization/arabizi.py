"""Arabizi (Latin-script Darija) -> Arabic script.

Two layers:
  1. a word lexicon learned from aligned data (see lexicon.py), used when the word is known
  2. context-free rules as a fallback for unknown words (the rules cannot know where a
     Darija speaker would write a long vowel, so they are only an approximation)
"""
import re
import unicodedata

from darijabridge.normalization.orthography import GAF

_AR_QMARK, _AR_COMMA, _AR_SEMI = "\u061f", "\u060c", "\u061b"

DIGITS = {"2": "\u0621", "3": "\u0639", "4": "\u063a", "5": "\u062e",
          "6": "\u0637", "7": "\u062d", "8": "\u063a", "9": "\u0642"}
DIGRAPHS = {"kh": "\u062e", "gh": "\u063a", "ch": "\u0634", "sh": "\u0634", "th": "\u062b",
            "dh": "\u0630", "ou": "\u0648", "oo": "\u0648", "aa": "\u0627", "ii": "\u064a", "ee": "\u064a"}
LETTERS = {"b": "\u0628", "t": "\u062a", "j": "\u062c", "d": "\u062f", "r": "\u0631", "z": "\u0632",
           "s": "\u0633", "f": "\u0641", "k": "\u0643", "l": "\u0644", "m": "\u0645", "n": "\u0646",
           "h": "\u0647", "w": "\u0648", "y": "\u064a", "q": "\u0642", "g": GAF, "p": "\u0628",
           "v": "\u0641", "x": "\u0634", "c": "\u0643"}
# Vowels were tuned on a held-out part of DODA: every a/i/o/u is written, e only at word start.
VOWELS = {"a": "\u0627", "i": "\u064a", "o": "\u0648", "u": "\u0648"}
_REPEAT = re.compile(r"(.)\1+")
WORD = re.compile(r"[^\W_]+")
LATIN = re.compile("[A-Za-z\u00C0-\u00FF]")


def _strip_accents(word: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", word) if not unicodedata.combining(c))


def rules_transliterate(word: str) -> str:
    """Rule-based fallback. Digits-only words are returned unchanged."""
    w = _strip_accents(word.lower())
    if w.isdigit():
        return w
    out, i, n = [], 0, len(w)
    while i < n:
        pair = w[i:i + 2]
        ch = w[i]
        if pair in DIGRAPHS:
            out.append(DIGRAPHS[pair]); i += 2; continue
        if ch == "2" and i == 0:
            out.append("\u0627")                      # initial hamza: written on an alef
        elif ch in DIGITS:
            out.append(DIGITS[ch])
        elif ch in VOWELS:
            out.append(VOWELS[ch])
        elif ch == "e":
            if i == 0:
                out.append("\u0627")
        else:
            out.append(LETTERS.get(ch, ch))
        i += 1
    return _REPEAT.sub(r"\1", "".join(out))            # 'rr' -> single letter (shadda is not written)


class Transliterator:
    def __init__(self, lexicon: dict[str, str] | None = None, arabic_punct: bool = True):
        self.lexicon = lexicon or {}
        self.arabic_punct = arabic_punct

    def word(self, token: str) -> tuple[str, bool]:
        """Returns (arabic_word, found_in_lexicon)."""
        known = self.lexicon.get(token.lower())
        if known is not None:
            return known, True
        return rules_transliterate(token), False

    def sentence(self, text: str) -> tuple[str, int, int]:
        """Transliterates every token that contains Latin letters (or digits mixed with them).
        Returns (text, n_latin_tokens, n_unknown_tokens)."""
        counts = [0, 0]

        def repl(m: re.Match) -> str:
            tok = m.group()
            if not LATIN.search(tok):
                return tok                              # Arabic word or pure number: untouched
            arabic, known = self.word(tok)
            counts[0] += 1
            counts[1] += not known
            return arabic

        out = WORD.sub(repl, text)
        if self.arabic_punct and re.search("[\u0600-\u06FF]", out):
            out = out.replace("?", _AR_QMARK).replace(",", _AR_COMMA).replace(";", _AR_SEMI)
        return out, counts[0], counts[1]
