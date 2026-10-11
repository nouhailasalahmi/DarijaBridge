from darijabridge.normalization.arabizi import Transliterator, rules_transliterate
from darijabridge.normalization.evaluate import edit_distance, evaluate, is_test
from darijabridge.normalization.lexicon import build_lexicon
from darijabridge.normalization.orthography import normalize_arabic
from darijabridge.normalization.pipeline import Normalizer
from darijabridge.normalization.script_detection import script_of


def test_script_of():
    assert script_of("kanbghik bzaf") == "latin"
    assert script_of("\u0643\u0646\u0628\u063a\u064a\u0643") == "arabic"
    assert script_of("rani \u0645\u0631\u0643\u0632") == "mixed"
    assert script_of("123 !!") == "none"


def test_normalize_arabic():
    assert normalize_arabic("\u0623\u0646\u0627") == "\u0627\u0646\u0627"                    # أنا -> انا
    assert normalize_arabic("\u0645\u064f\u0631\u064e\u0643\u0651\u0632") == "\u0645\u0631\u0643\u0632"  # diacritics
    assert normalize_arabic("\u0661\u0662") == "12"


def test_rules():
    assert rules_transliterate("7lib") == "\u062d\u0644\u064a\u0628"          # حليب
    assert rules_transliterate("chkoun") == "\u0634\u0643\u0648\u0646"        # شكون
    assert rules_transliterate("mrrra") == "\u0645\u0631\u0627"               # doubled letters collapse
    assert rules_transliterate("2ana") == "\u0627\u0646\u0627"                # initial 2 -> alef
    assert rules_transliterate("32") == "32"                                   # numbers untouched


def test_lexicon_and_sentence():
    lex = build_lexicon([("kandir lwe9t", "\u0643\u0646\u0636\u064a\u0631 \u0627\u0644\u0648\u0642\u062a")])
    assert lex["kandir"] == "\u0643\u0646\u0636\u064a\u0631"
    t = Transliterator(lex)
    text, n, unk = t.sentence("kandir 7lib?")
    assert text.startswith("\u0643\u0646\u0636\u064a\u0631 ") and text.endswith("\u061f")
    assert (n, unk) == (2, 1)


def test_arabic_words_and_numbers_untouched_in_mixed_text():
    r = Normalizer().normalize("rani \u0645\u0631\u0643\u0632 32")
    assert r.text.split()[1:] == ["\u0645\u0631\u0643\u0632", "32"] and r.script == "mixed"


def test_record_keeps_cleaned_text():
    rec = {"id": "x", "text_darija": "salam", "meta": {}}
    out = Normalizer().normalize_record(rec)
    assert out["text_darija"] == "salam" and out["text_darija_norm"] and out["meta"]["script"] == "latin"


def test_eval_helpers():
    assert edit_distance("abc", "abd") == 1
    assert is_test("abc") == is_test("abc")
    m = evaluate(Transliterator({"salam": "\u0633\u0644\u0627\u0645"}), [("salam", "\u0633\u0644\u0627\u0645")])
    assert m["word_accuracy"] == 1.0 and m["oov_rate"] == 0.0


def test_reference_field_is_stored_normalized():
    norm = Normalizer(reference_field="darija_ar")
    rec = {"id": "x", "text_darija": "ana", "meta": {"darija_ar": "\u0623\u0646\u0627?"}}
    out = norm.normalize_record(rec)
    assert out["text_darija_ar_ref"] == "\u0627\u0646\u0627\u061f"      # alef unified, Arabic question mark
    assert "text_darija_ar_ref" not in Normalizer().normalize_record(rec)  # off unless configured
