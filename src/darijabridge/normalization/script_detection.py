import re

_ARABIC = re.compile("[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
_LATIN = re.compile("[A-Za-z\u00C0-\u00FF]")


def has_arabic(text: str) -> bool:
    return bool(_ARABIC.search(text))


def has_latin(text: str) -> bool:
    return bool(_LATIN.search(text))


def script_of(text: str) -> str:
    """'arabic', 'latin' (Arabizi or other Latin text), 'mixed' or 'none' (no letters)."""
    ar, lat = has_arabic(text), has_latin(text)
    if ar and lat:
        return "mixed"
    return "arabic" if ar else "latin" if lat else "none"
