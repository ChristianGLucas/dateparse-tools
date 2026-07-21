from gen.messages_pb2 import DateTimeSearchRequest, ParseOptions
from nodes.search_date_time_expressions import search_date_time_expressions
from nodes.testkit import FakeContext

BASE = "2026-01-01T00:00:00"


def run(text, base_time=BASE, **opt_kwargs):
    ax = FakeContext()
    return search_date_time_expressions(
        ax, DateTimeSearchRequest(text=text, base_time=base_time, options=ParseOptions(**opt_kwargs))
    )


def test_finds_multiple_expressions_with_correct_positions_and_values():
    text = "Let's meet next week or tomorrow at 5pm, whichever works. Also March 3rd works."
    r = run(text, languages=["en"])
    assert r.error.code == ""
    assert [m.text for m in r.matches] == ["next week", "tomorrow at 5pm", "March 3rd"]
    assert [m.datetime for m in r.matches] == [
        "2026-01-08T00:00:00",
        "2026-01-02T17:00:00",
        "2026-03-03T00:00:00",
    ]
    # start_index must point at the real position of the match in the
    # ORIGINAL text -- verified by slicing the source with it.
    for m in r.matches:
        assert text[m.start_index : m.start_index + len(m.text)] == m.text


def test_tolerates_irregular_whitespace_inside_a_match():
    # dateparser's search normalizes whitespace before matching ("next   week"
    # is reported back as "next week"); this node must recover the ORIGINAL
    # substring and its real position, not the normalized one.
    text = "Let's meet  next   week please."
    r = run(text, languages=["en"])
    assert len(r.matches) == 1
    m = r.matches[0]
    assert m.text == "next   week"
    assert text[m.start_index : m.start_index + len(m.text)] == "next   week"
    assert m.datetime == "2026-01-08T00:00:00"


def test_unambiguous_iso_date_is_found_under_the_default_language_shortlist():
    r = run("See you on 2026-03-05 for the review.")
    assert [m.text for m in r.matches] == ["2026-03-05"]
    assert r.matches[0].datetime == "2026-03-05T00:00:00"


def test_no_dates_returns_empty_matches_not_an_error():
    r = run("no dates anywhere in this sentence")
    assert list(r.matches) == []
    assert r.error.code == ""


def test_repeated_invocation_is_deterministic():
    text = "Meet me on 2026-03-05."
    a = run(text)
    b = run(text)
    assert [m.datetime for m in a.matches] == [m.datetime for m in b.matches]


def test_empty_text_is_a_structured_error():
    r = run("")
    assert r.error.code == "INVALID_INPUT"


def test_missing_base_time_is_a_structured_error():
    r = run("2026-03-05", base_time="")
    assert r.error.code == "INVALID_INPUT"


def test_oversized_text_is_rejected_as_too_large():
    r = run("x" * 20001)
    assert r.error.code == "TOO_LARGE"
