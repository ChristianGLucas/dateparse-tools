from gen.messages_pb2 import PhraseLanguageRequest
from nodes.detect_phrase_language import detect_phrase_language
from nodes.testkit import FakeContext


def run(text, candidate_languages=()):
    ax = FakeContext()
    return detect_phrase_language(
        ax, PhraseLanguageRequest(text=text, candidate_languages=list(candidate_languages))
    )


def test_detects_french():
    r = run("il y a 2 heures")
    assert r.recognized is True
    assert r.language == "fr"
    assert r.error.code == ""


def test_detects_english():
    r = run("3 days ago")
    assert r.recognized is True
    assert r.language == "en"


def test_detects_german():
    r = run("vor 2 Stunden")
    assert r.recognized is True
    assert r.language == "de"


def test_unrecognizable_phrase_returns_recognized_false_not_an_error():
    r = run("not a date whatsoever zzz")
    assert r.recognized is False
    assert r.language == ""
    assert r.error.code == ""


def test_candidate_languages_restricts_the_search():
    # "3 days ago" only matches an English pattern; restricting the
    # candidates to French forces a miss even though the text is a real,
    # recognizable date expression in English.
    r = run("3 days ago", candidate_languages=["fr"])
    assert r.recognized is False


def test_repeated_invocation_is_deterministic():
    a = run("il y a 2 heures")
    b = run("il y a 2 heures")
    assert a.language == b.language == "fr"


def test_empty_text_is_a_structured_error():
    r = run("")
    assert r.error.code == "INVALID_INPUT"


def test_unknown_candidate_language_is_a_structured_error():
    r = run("hello", candidate_languages=["zz-not-a-real-code"])
    assert r.error.code == "INVALID_INPUT"
