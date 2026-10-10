from darijabridge.cleaning.alignment import check_pair
from darijabridge.cleaning.dedup import Deduper
from darijabridge.cleaning.filters import check_text
from darijabridge.cleaning.text_ops import clean_text

F = {}


def test_nfkc_fixes_arabic_presentation_forms():
    text, changed = clean_text("\ufe8d\ufedf\ufe92\ufe8e\ufe95")   # presentation forms
    assert text == "\u0627\u0644\u0628\u0627\u062a" and "nfkc" in changed


def test_html_tags_and_broken_entities():
    assert clean_text("a < br > b")[0] == "a b"
    assert clean_text("it & # 39 ; s ok")[0] == "it's ok"
    assert clean_text("&amp;#39;x")[0] == "'x"


def test_urls_mentions_removed_but_email_kept_for_filter():
    assert clean_text("@ali salam https://x.co/a")[0] == "salam"
    assert "@" in clean_text("write to me@mail.com")[0]


def test_emojis_and_repeats():
    assert clean_text("bravo \U0001F602\U0001F602")[0] == "bravo"
    assert clean_text("sa7iiiiii")[0] == "sa7ii"
    assert clean_text("wow!!!!!!")[0] == "wow!!!"
    assert clean_text("2000")[0] == "2000"            # digits are never collapsed


def test_arabic_text_untouched():
    s = "\u0643\u0646\u062f\u064a\u0631 \u0627\u0644\u0648\u0642\u062a"
    assert clean_text(s) == (s, [])


def test_check_text_reasons():
    assert check_text("", F) == "empty"
    assert check_text("a", F) == "too_short"
    assert check_text("12345", F) == "no_letters"
    assert check_text("ab !!! ??? ...", F) == "mostly_non_text"
    assert check_text("3ta9!", F) is None                          # Arabizi digits are letters
    assert check_text("7lib...?", F) is None
    assert check_text("3ndi 32", F) is None
    assert check_text("call 0612345678 now", F) == "contact_info"
    assert check_text("me@mail.com", F) == "contact_info"
    assert check_text("kanbghik bzaf", F) is None
    assert check_text("mot " * 101, F) == "too_long"


def test_check_pair():
    assert check_pair("hello world friend", "Hello World Friend", F) == "identical_pair"
    assert check_pair("ok", "ok", F) is None                       # too short to judge
    assert check_pair("salam", "hello how are you doing today my friend", F) == "length_ratio"
    assert check_pair("kanbghik bzaf", "I love you a lot", F) is None


def test_dedup():
    d = Deduper()
    assert d.check("a", "Salam", "Hello") is None
    assert d.check("a", "salam", "hello") == "duplicate_in_source"
    assert d.check("b", "SALAM", "HELLO") == "duplicate_other_source"
    assert d.check("a", "salam", None) is None                    # different key (no translation)
