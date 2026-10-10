"""Rules about a (darija, translation) PAIR."""


def check_pair(darija: str, target: str, f: dict) -> str | None:
    wd, wt = len(darija.split()), len(target.split())
    if wd >= f.get("identical_pair_min_words", 3) and darija.casefold() == target.casefold():
        return "identical_pair"           # translation is a copy of the source
    ratio = (max(wd, wt) + 1) / (min(wd, wt) + 1)
    if ratio > f.get("max_len_ratio", 4.0):
        return "length_ratio"             # lengths too different: probably misaligned
    return None
