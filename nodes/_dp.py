"""Shared marshalling between this package's messages and dateparser.

dateparser owns the algorithmically hard part: recognizing a date/time
expression in one of ~200 languages and resolving it to an instant. This
module does three jobs around it, and deliberately nothing more:

1. **Deterministic timezone handling.** dateparser's own default `TIMEZONE`
   setting is `"local"` -- the deploying HOST's system zone -- which would
   make timezone-aware output depend on which machine answered the request.
   This module never leaves that default in play: it is always either left
   alone entirely (naive in, naive out) or pinned to an explicit zone name
   ("UTC", or the caller's `assume_timezone`), never "local".

2. **A single base_time contract.** Every relative expression resolves
   against RELATIVE_BASE, and RELATIVE_BASE always comes from the caller's
   `base_time`, never from wall-clock `now()`. An aware base_time (carrying
   a UTC offset) yields aware output; a naive one yields naive output --
   this policy is what keeps the awareness of the output predictable from
   the request alone, rather than from what the matched text happened to
   contain.

3. **A stable error contract.** Anything dateparser or this module rejects
   comes back as an Error{code, message} instead of a raised exception
   reaching the caller.

Byte-size / input-length / batch-count limits are not this module's job --
the platform owns request-size and resource limits. This module still
defaults an unfiltered language search to a compact common-language
shortlist (see DEFAULT_LANGUAGES) rather than the library's full ~200
locales, purely because that materially narrows the DEFAULT match
candidates -- a caller who wants the full search still gets it by passing
an explicit, wider `languages` list.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Tuple

from dateutil import parser as _dateutil_parser


class DPError(Exception):
    """A deterministic, caller-facing rejection carrying a stable code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def err(code: str, message: str) -> DPError:
    return DPError(code, message)


# A compact shortlist of widely-used languages, used whenever a caller does
# not narrow the search themselves. Bounds worst-case latency to roughly
# 20-30ms even on unparseable input (measured), against 30-280ms unrestricted
# across the full bundled locale set -- see module docstring point 1.
DEFAULT_LANGUAGES: Tuple[str, ...] = (
    "en", "es", "fr", "de", "pt", "it", "nl", "ru", "zh", "ja",
    "ko", "ar", "hi", "tr", "pl", "uk", "sv", "id",
)


def _load_supported_languages() -> Tuple[str, ...]:
    """The full set of language/locale codes dateparser's bundled data
    recognizes, read from the library itself rather than hand-copied, so it
    never drifts from whatever dateparser version is pinned.
    """
    from dateparser.languages.loader import LocaleDataLoader

    return tuple(sorted(locale.shortname for locale in LocaleDataLoader().get_locales()))


SUPPORTED_LANGUAGES: Tuple[str, ...] = _load_supported_languages()
_SUPPORTED_SET = set(SUPPORTED_LANGUAGES)

_PREFER_DATES_FROM = {"current_period", "future", "past"}
_DATE_ORDER = {"MDY", "DMY", "YMD"}


def check_text(text: str, field: str) -> str:
    if text is None or text == "":
        raise err("INVALID_INPUT", f"{field} is required and must not be empty")
    return text


def validate_languages(codes: Iterable[str], field: str) -> List[str]:
    codes = list(codes)
    if not codes:
        return list(DEFAULT_LANGUAGES)
    for code in codes:
        if code not in _SUPPORTED_SET:
            raise err(
                "INVALID_INPUT",
                f"{field} entry '{code}' is not a language code dateparser's "
                f"bundled data recognizes (see ListSupportedLanguages)",
            )
    return codes


def check_timezone(name: str, field: str) -> str:
    """Validate an IANA zone name against Python's own tzdata, so an unknown
    zone is reported as INVALID_INPUT rather than falling through to
    dateparser's UnknownTimeZoneError and surfacing as INTERNAL.
    """
    from zoneinfo import available_timezones

    if name not in available_timezones():
        raise err(
            "INVALID_INPUT",
            f"{field} '{name}' is not a known IANA time zone name",
        )
    return name


def parse_base_time(value: str, field: str = "base_time") -> Tuple[datetime, bool]:
    """Parse an RFC 3339 / ISO 8601 instant. Returns (datetime, is_aware)."""
    if value is None or value == "":
        raise err("INVALID_INPUT", f"{field} is required and must not be empty")
    try:
        dt = _dateutil_parser.isoparse(value)
    except (ValueError, OverflowError) as exc:
        raise err(
            "INVALID_INPUT",
            f"{field} '{value}' is not a valid RFC 3339 / ISO 8601 "
            f"instant: {exc}",
        )
    return dt, dt.tzinfo is not None


def build_settings(base_time: str, options) -> Tuple[dict, List[str], bool]:
    """Turn a base_time string + ParseOptions into dateparser settings.

    Returns (settings, languages, is_aware). `is_aware` tells the caller
    whether the resolved output will carry a UTC offset, so callers that also
    need to format an empty/absent result stay consistent.
    """
    base_dt, is_aware = parse_base_time(base_time)

    settings: dict = {
        # Without this, dateparser reports "day" as the period for a bare
        # time-of-day match (e.g. "5pm") just like it does for a full
        # calendar date -- collapsing the one distinction `period` exists to
        # make. With it, a bare time-of-day match is reported as "time".
        "RETURN_TIME_AS_PERIOD": True,
    }
    if is_aware:
        # Pin to UTC explicitly rather than leaving dateparser's TIMEZONE
        # default ("local", the host's own zone) in play -- see module
        # docstring point 2. The base itself is normalized to naive UTC so
        # RELATIVE_BASE math is not tied to a specific tzinfo implementation.
        settings["RELATIVE_BASE"] = base_dt.astimezone(timezone.utc).replace(tzinfo=None)
        settings["TIMEZONE"] = "UTC"
        settings["RETURN_AS_TIMEZONE_AWARE"] = True
    else:
        settings["RELATIVE_BASE"] = base_dt

    assume_tz = getattr(options, "assume_timezone", "") if options is not None else ""
    convert_tz = getattr(options, "convert_to_timezone", "") if options is not None else ""

    if assume_tz:
        settings["TIMEZONE"] = check_timezone(assume_tz, "options.assume_timezone")
        settings["RETURN_AS_TIMEZONE_AWARE"] = True

    if convert_tz:
        if not (assume_tz or is_aware):
            raise err(
                "INVALID_INPUT",
                "options.convert_to_timezone requires options.assume_timezone "
                "or an aware base_time (one carrying a UTC offset) -- "
                "otherwise there is no source zone to convert from",
            )
        settings["TO_TIMEZONE"] = check_timezone(convert_tz, "options.convert_to_timezone")
        settings["RETURN_AS_TIMEZONE_AWARE"] = True

    prefer = getattr(options, "prefer_dates_from", "") if options is not None else ""
    if prefer:
        if prefer not in _PREFER_DATES_FROM:
            raise err(
                "INVALID_INPUT",
                f"options.prefer_dates_from '{prefer}' must be one of "
                f"{sorted(_PREFER_DATES_FROM)}",
            )
        settings["PREFER_DATES_FROM"] = prefer

    order = getattr(options, "date_order", "") if options is not None else ""
    if order:
        if order not in _DATE_ORDER:
            raise err(
                "INVALID_INPUT",
                f"options.date_order '{order}' must be one of {sorted(_DATE_ORDER)}",
            )
        settings["DATE_ORDER"] = order

    if options is not None and getattr(options, "strict_parsing", False):
        settings["STRICT_PARSING"] = True

    languages_field = list(options.languages) if options is not None else []
    languages = validate_languages(languages_field, "options.languages")

    aware_result = "RETURN_AS_TIMEZONE_AWARE" in settings and settings["RETURN_AS_TIMEZONE_AWARE"]
    return settings, languages, aware_result


def resolve(text: str, settings: dict, languages: List[str]):
    """Run dateparser and return its DateData (date_obj, period, locale)."""
    from dateparser.date import DateDataParser

    parser = DateDataParser(languages=languages, settings=settings)
    return parser.get_date_data(text)


_WS = re.compile(r"\s+")


def locate_matches(text: str, matches: List[Tuple[str, datetime]]) -> List[Tuple[str, int, datetime]]:
    """Recover each dateparser search match's real substring and position.

    dateparser.search.search_dates normalizes whitespace before matching, so
    its matched strings do not always reappear verbatim in the original text
    (e.g. "next   week" is returned as "next week"). This rebuilds a
    whitespace-tolerant pattern from the matched tokens to locate the real
    span, so `text`/`start_index` describe the caller's own original text,
    not dateparser's internal normalization of it.
    """
    out: List[Tuple[str, int, datetime]] = []
    cursor = 0
    for matched, dt in matches:
        tokens = matched.split()
        if not tokens:
            continue
        pattern = r"\s+".join(re.escape(tok) for tok in tokens)
        found = re.search(pattern, text[cursor:])
        if found is None:
            found = re.search(pattern, text)
            start = found.start() if found else -1
            end = found.end() if found else -1
        else:
            start = cursor + found.start()
            end = cursor + found.end()
        if start == -1:
            # Could not relocate the span (should not happen given dateparser
            # only ever returns substrings of the text it was given) -- report
            # the library's own matched text with no reliable position rather
            # than silently drop or mis-locate the match.
            out.append((matched, -1, dt))
            continue
        out.append((text[start:end], start, dt))
        cursor = end
    return out
