"""Independent oracles: every expected value below is computed by hand from
the stated base_time (calendar/clock arithmetic, or UTC-offset arithmetic),
not by running dateparser and recording what it did. That is what makes this
an oracle rather than a change-detector.
"""

from gen.messages_pb2 import NaturalDateTimeRequest, ParseOptions
from nodes.parse_natural_date_time import parse_natural_date_time
from nodes.testkit import FakeContext


def run(text, base_time, **opt_kwargs):
    ax = FakeContext()
    return parse_natural_date_time(
        ax,
        NaturalDateTimeRequest(text=text, base_time=base_time, options=ParseOptions(**opt_kwargs)),
    )


# base_time is a Thursday.
BASE = "2026-01-01T00:00:00"


def test_relative_days_ago_resolves_against_base_time_not_wall_clock():
    r = run("3 days ago", BASE)
    assert r.found is True
    assert r.datetime == "2025-12-29T00:00:00"
    assert r.error.code == ""


def test_relative_period_words():
    assert run("yesterday", BASE).datetime == "2025-12-31T00:00:00"
    assert run("next month", BASE).datetime == "2026-02-01T00:00:00"
    assert run("next month", BASE).period == "month"
    assert run("next year", BASE).datetime == "2027-01-01T00:00:00"


def test_relative_time_of_day():
    r = run("tomorrow at 5pm", BASE)
    assert r.datetime == "2026-01-02T17:00:00"
    # An explicit clock time in the match reports "time", regardless of
    # whether the date portion was stated or filled in from base_time.
    assert r.period == "time"


def test_bare_clock_time_reports_time_period():
    r = run("5pm", BASE)
    assert r.datetime == "2026-01-01T17:00:00"
    assert r.period == "time"


def test_date_only_expression_reports_day_period_even_when_relative():
    # "3 days ago" has no clock-time component, so it stays "day" even
    # though it is a purely relative delta rather than a stated calendar date.
    assert run("3 days ago", BASE).period == "day"


def test_french_relative_expression_and_detected_language():
    # "2 hours ago" in French. 00:00 minus 2h crosses back to the prior day.
    r = run("il y a 2 heures", BASE)
    assert r.found is True
    assert r.datetime == "2025-12-31T22:00:00"
    assert r.detected_language == "fr"


def test_absolute_date():
    r = run("2026-03-01", BASE)
    assert r.found is True
    assert r.datetime.startswith("2026-03-01")


def test_ambiguous_numeric_date_honours_date_order_setting():
    # "01/02/2026" is genuinely ambiguous: Jan 2 under MDY, Feb 1 under DMY.
    assert run("01/02/2026", BASE, date_order="MDY").datetime == "2026-01-02T00:00:00"
    assert run("01/02/2026", BASE).datetime == "2026-01-02T00:00:00"  # MDY is the default
    assert run("01/02/2026", BASE, date_order="DMY").datetime == "2026-02-01T00:00:00"


def test_prefer_dates_from_future_resolves_a_bare_weekday_forward():
    # base_time (2026-01-01) is a Thursday; the next Friday is 2026-01-02.
    r = run("Friday", BASE, prefer_dates_from="future")
    assert r.datetime == "2026-01-02T00:00:00"


def test_assume_timezone_interprets_a_naive_result_in_the_given_zone():
    r = run("2026-01-15 10:00", BASE, assume_timezone="America/New_York")
    assert r.datetime == "2026-01-15T10:00:00-05:00"


def test_convert_to_timezone_converts_the_resolved_instant():
    r = run("2026-01-15 10:00", BASE, assume_timezone="America/New_York", convert_to_timezone="UTC")
    assert r.datetime == "2026-01-15T15:00:00+00:00"


def test_aware_base_time_yields_aware_output_pinned_to_utc():
    # 2026-01-01T00:00:00-05:00 is 2026-01-01T05:00:00Z; 3 days earlier is
    # 2025-12-29T05:00:00Z. Hand-computed UTC-offset arithmetic, independent
    # of any dateparser internals.
    r = run("3 days ago", "2026-01-01T00:00:00-05:00")
    assert r.datetime == "2025-12-29T05:00:00+00:00"


def test_naive_base_time_yields_naive_output():
    r = run("3 days ago", BASE)
    assert "+" not in r.datetime and "Z" not in r.datetime


def test_text_with_no_date_returns_found_false_not_an_error():
    r = run("this is not a date at all zzz", BASE)
    assert r.found is False
    assert r.datetime == ""
    assert r.error.code == ""


def test_repeated_invocation_is_deterministic():
    a = run("3 days ago", BASE)
    b = run("3 days ago", BASE)
    assert a.datetime == b.datetime == "2025-12-29T00:00:00"


def test_empty_text_is_a_structured_error_not_a_crash():
    r = run("", BASE)
    assert r.error.code == "INVALID_INPUT"
    assert r.found is False


def test_missing_base_time_is_a_structured_error():
    r = run("3 days ago", "")
    assert r.error.code == "INVALID_INPUT"


def test_malformed_base_time_is_a_structured_error():
    r = run("3 days ago", "not-a-timestamp")
    assert r.error.code == "INVALID_INPUT"


def test_unknown_language_code_is_a_structured_error():
    r = run("3 days ago", BASE, languages=["xx-nonexistent"])
    assert r.error.code == "INVALID_INPUT"


def test_invalid_prefer_dates_from_is_a_structured_error():
    r = run("3 days ago", BASE, prefer_dates_from="sideways")
    assert r.error.code == "INVALID_INPUT"


def test_invalid_date_order_is_a_structured_error():
    r = run("3 days ago", BASE, date_order="ABC")
    assert r.error.code == "INVALID_INPUT"


def test_convert_to_timezone_without_a_source_zone_is_a_structured_error():
    r = run("3 days ago", BASE, convert_to_timezone="UTC")
    assert r.error.code == "INVALID_INPUT"


def test_unknown_assume_timezone_is_a_structured_invalid_input_error():
    # Must not fall through to dateparser's own UnknownTimeZoneError and
    # surface as INTERNAL -- the caller's mistake belongs in INVALID_INPUT.
    r = run("3 days ago", BASE, assume_timezone="Not/ARealZone")
    assert r.error.code == "INVALID_INPUT"


def test_unknown_convert_to_timezone_is_a_structured_invalid_input_error():
    r = run(
        "3 days ago", BASE,
        assume_timezone="America/New_York", convert_to_timezone="Not/ARealZone",
    )
    assert r.error.code == "INVALID_INPUT"


def test_bare_next_weekday_phrasing_is_a_known_dateparser_gap():
    # Documented, tested limitation (not this package's own bug): dateparser
    # 1.4.1 fails to parse "next <weekday>" phrasing entirely -- it returns
    # no match rather than a wrong one. A bare weekday name ("Friday") DOES
    # parse (see test_prefer_dates_from_future_resolves_a_bare_weekday_forward
    # above), so that is the supported way to express the same intent. This
    # test pins the gap so a future dateparser upgrade that fixes it is
    # noticed (the assertion would then fail, prompting an update here) and
    # so no shipped text at this version claims "next Friday" support.
    r = run("next Friday", BASE)
    assert r.found is False
    assert r.error.code == ""
