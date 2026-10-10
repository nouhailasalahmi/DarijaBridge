"""Rules that decide whether ONE text is usable. Return a reject reason or None."""
import re

_LETTER = re.compile(r"[^\W\d_]")
_ALNUM = re.compile(r"[^\W_]")      # letters AND digits: in Arabizi, 3 7 9 5 8 are letters
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"\d(?:[\s.-]?\d){8,}")   # 9+ digits, possibly separated


def check_text(text: str, f: dict) -> str | None:
    if not text:
        return "empty"
    if f.get("reject_contact_info", True) and (_EMAIL.search(text) or _PHONE.search(text)):
        return "contact_info"
    if len(text) < f.get("min_chars", 2):
        return "too_short"
    if len(text.split()) > f.get("max_words", 100):
        return "too_long"
    if not _LETTER.search(text):
        return "no_letters"
    alnum = len(_ALNUM.findall(text))
    if alnum / len(text.replace(" ", "")) < f.get("min_alnum_ratio", 0.5):
        return "mostly_non_text"
    return None
