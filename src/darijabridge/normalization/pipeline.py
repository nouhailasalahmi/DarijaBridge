from dataclasses import dataclass

from darijabridge.cleaning.text_ops import clean_text
from darijabridge.normalization.arabizi import Transliterator
from darijabridge.normalization.orthography import normalize_arabic
from darijabridge.normalization.script_detection import script_of


@dataclass
class NormResult:
    text: str
    script: str            # script of the input: arabic / latin / mixed / none
    n_latin_tokens: int
    n_unknown_tokens: int  # latin tokens not found in the lexicon (rule-based guess)


class Normalizer:
    """Single entry point, used both for the dataset and (later) for user queries in the demo."""

    def __init__(self, lexicon: dict[str, str] | None = None, arabic_punct: bool = True,
                 unify_gaf: bool = True, reference_field: str | None = None):
        self.translit = Transliterator(lexicon, arabic_punct)
        self.unify_gaf = unify_gaf
        self.reference_field = reference_field   # meta key holding a reference Arabic text (DODA: darija_ar)

    def normalize_reference(self, text: str) -> str:
        """Same cleaning and orthography as the predicted text, applied to a reference Arabic text."""
        text, _ = clean_text(text)
        text = normalize_arabic(text, self.unify_gaf)
        if self.translit.arabic_punct:
            text = text.replace("?", "\u061f").replace(",", "\u060c").replace(";", "\u061b")
        return text

    def normalize(self, text: str) -> NormResult:
        script = script_of(text)
        text = normalize_arabic(text, self.unify_gaf)
        text, n_lat, n_unk = self.translit.sentence(text)
        return NormResult(text, script, n_lat, n_unk)

    def normalize_record(self, rec: dict) -> dict:
        """Keeps text_darija (cleaned) and adds:
          text_darija_norm    prediction (what a user typing Arabizi would get through the pipeline)
          text_darija_ar_ref  reference Arabic text provided by the source, when there is one (DODA)
        plus script information in meta."""
        r = self.normalize(rec["text_darija"])
        meta = dict(rec.get("meta") or {}, script=r.script)
        if r.n_latin_tokens:
            meta["translit_unknown_ratio"] = round(r.n_unknown_tokens / r.n_latin_tokens, 3)
        out = dict(rec, text_darija_norm=r.text, meta=meta)
        if self.reference_field:
            ref = (rec.get("meta") or {}).get(self.reference_field)
            ref = self.normalize_reference(ref) if ref else ""
            if ref:
                out["text_darija_ar_ref"] = ref
        return out
