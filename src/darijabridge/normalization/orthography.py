"""Orthographic normalization of Arabic-script text.

Goal: one written form per word, so that the model does not see 'the same word'
under several spellings. Choices are deliberately conservative:
  - diacritics and tatweel removed (they are optional and rarely written in Darija)
  - alef variants unified, alef maqsura -> ya, Arabic-Indic digits -> ASCII digits
  - gaf variants unified to the Moroccan letter (optional: check your tokenizer covers it)
Ta marbuta (ة) is NOT merged with ha (ه): that would erase a real distinction.
"""
import re
import unicodedata

_DIACRITICS = re.compile("[\u064b-\u065f\u0670\u0640]")     # tashkeel + superscript alef + tatweel
_ALEF = re.compile("[\u0623\u0625\u0622\u0671]")           # أ إ آ ٱ -> ا
_ARABIC_DIGITS = str.maketrans("\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669", "0123456789")
GAF_VARIANTS = ("\u06af", "\u0763")                         # گ and ݣ
GAF = "\u06ad"                                              # ڭ


def normalize_arabic(text: str, unify_gaf: bool = True) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = _DIACRITICS.sub("", text)
    text = _ALEF.sub("\u0627", text)
    text = text.replace("\u0649", "\u064a")
    text = text.translate(_ARABIC_DIGITS)
    if unify_gaf:
        for g in GAF_VARIANTS:
            text = text.replace(g, GAF)
    return text
