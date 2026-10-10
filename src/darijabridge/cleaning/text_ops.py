"""Character-level cleaning steps (str -> str).

None of them is meant to change the meaning of a sentence: they remove artifacts
(HTML leftovers, invisible characters, emojis, URLs...) and fix Unicode forms.
Orthographic normalization (Arabizi, spelling variants...) belongs to part 3.
"""
import html
import re
import unicodedata

_INVISIBLE = re.compile("[\u200b-\u200f\u202a-\u202e\u2060-\u2069\ufeff\u00ad]")
_CONTROL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_APOSTROPHE_ENTITY = re.compile(r"(?<=\w)\s*&\s*#\s*(?:39|x27)\s*;\s*(?=\w)", re.I)
_SPACED_NUM_ENTITY = re.compile(r"&\s*#\s*(x[0-9a-fA-F]+|\d+)\s*;")
_SPACED_NAMED_ENTITY = re.compile(r"&\s*(amp|quot|lt|gt|apos|nbsp)\s*;", re.I)
_TAG = re.compile(r"<\s*/?\s*(?:br|p|div|span|b|i|u|em|strong|a|li|ul|ol|h[1-6]|img|font)\b[^<>]*>", re.I)
_URL = re.compile(r"(?:https?://|www\.)\S+", re.I)
_MENTION = re.compile(r"(?<![\w.])@\w+")
_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\uFE0F\u20E3]"
)
_LETTER_REPEAT = re.compile(r"([^\W\d_])\1{2,}")
_PUNCT_REPEAT = re.compile(r"([!?.\u060c\u061f*~_=-])\1{3,}")
_SPACES = re.compile(r"\s+")


def nfkc(t: str) -> str:
    """Unicode compatibility form: turns Arabic presentation forms into plain letters."""
    return unicodedata.normalize("NFKC", t)


def invisible(t: str) -> str:
    return _CONTROL.sub("", _INVISIBLE.sub("", t))


def html_artifacts(t: str) -> str:
    """Decode entities (even broken ones like '& # 39 ;') and drop HTML tags (even '< br >')."""
    t = _APOSTROPHE_ENTITY.sub("'", t)          # tokenized "it & # 39 ; s" -> "it's"
    t = _SPACED_NUM_ENTITY.sub(lambda m: f"&#{m.group(1)};", t)
    t = _SPACED_NAMED_ENTITY.sub(lambda m: f"&{m.group(1).lower()};", t)
    for _ in range(2):  # handles double-escaped text
        decoded = html.unescape(t)
        if decoded == t:
            break
        t = decoded
    return _TAG.sub(" ", t)


def urls_mentions(t: str) -> str:
    return _MENTION.sub("", _URL.sub("", t))


def emojis(t: str) -> str:
    return _EMOJI.sub("", t)


def repeats(t: str) -> str:
    """'sa7iiiiii' -> 'sa7ii', '!!!!!!' -> '!!!'."""
    return _PUNCT_REPEAT.sub(r"\1\1\1", _LETTER_REPEAT.sub(r"\1\1", t))


def whitespace(t: str) -> str:
    return _SPACES.sub(" ", t).strip()


STEPS = {
    "nfkc": nfkc,
    "invisible": invisible,
    "html": html_artifacts,
    "urls_mentions": urls_mentions,
    "emojis": emojis,
    "repeats": repeats,
    "whitespace": whitespace,
}
DEFAULT_ORDER = list(STEPS)


def clean_text(text: str, steps: list[str] | None = None) -> tuple[str, list[str]]:
    """Apply the steps in order. Returns (cleaned_text, names_of_steps_that_changed_it)."""
    changed = []
    for name in steps or DEFAULT_ORDER:
        new = STEPS[name](text)
        if new != text:
            changed.append(name)
            text = new
    return text, changed
