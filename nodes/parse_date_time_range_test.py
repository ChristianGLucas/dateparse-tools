from gen.messages_pb2 import DateTimeRangeRequest, ParseOptions
from nodes.parse_date_time_range import parse_date_time_range
from nodes.testkit import FakeContext

BASE = "2026-01-01T00:00:00"


def run(start_text, end_text, base_time=BASE, **opt_kwargs):
    ax = FakeContext()
    return parse_date_time_range(
        ax,
        DateTimeRangeRequest(
            start_text=start_text, end_text=end_text, base_time=base_time,
            options=ParseOptions(**opt_kwargs),
        ),
    )


def test_resolves_both_ends_and_reports_ordered():
    r = run("March 1", "March 5")
    assert r.start_found is True and r.end_found is True
    assert r.start_datetime == "2026-03-01T00:00:00"
    assert r.end_datetime == "2026-03-05T00:00:00"
    assert r.ordered is True
    assert r.error.code == ""


def test_relative_ends_share_the_same_base_time():
    # Both resolve against the same base_time (2026-01-01), so this is
    # exactly the interval [2025-12-29, 2025-12-31].
    r = run("3 days ago", "1 day ago")
    assert r.start_datetime == "2025-12-29T00:00:00"
    assert r.end_datetime == "2025-12-31T00:00:00"
    assert r.ordered is True


def test_reversed_range_is_not_ordered_but_is_not_an_error():
    r = run("March 5", "March 1")
    assert r.start_found is True and r.end_found is True
    assert r.ordered is False
    assert r.error.code == ""


def test_one_end_not_found_is_not_ordered_and_not_an_error():
    r = run("March 1", "not a date at all zzz")
    assert r.start_found is True
    assert r.end_found is False
    assert r.end_datetime == ""
    assert r.ordered is False
    assert r.error.code == ""


def test_repeated_invocation_is_deterministic():
    a = run("March 1", "March 5")
    b = run("March 1", "March 5")
    assert (a.start_datetime, a.end_datetime) == (b.start_datetime, b.end_datetime)


def test_empty_start_text_is_a_structured_error():
    r = run("", "March 5")
    assert r.error.code == "INVALID_INPUT"


def test_empty_end_text_is_a_structured_error():
    r = run("March 1", "")
    assert r.error.code == "INVALID_INPUT"


def test_missing_base_time_is_a_structured_error():
    r = run("March 1", "March 5", base_time="")
    assert r.error.code == "INVALID_INPUT"
