from gen.messages_pb2 import DateTimeSearchRequest, FoundDateTimeExpressions, DateTimeMatch
from gen.axiom_context import AxiomContext

from nodes._dp import DPError, build_settings, check_text, locate_matches


def search_date_time_expressions(ax: AxiomContext, input: DateTimeSearchRequest) -> FoundDateTimeExpressions:
    """Find every natural-language date/time expression embedded in a longer
    passage of free text, each resolved against the same `base_time`, with
    the matched substring and its position in the original text.

    An empty `matches` list is a normal negative result -- the passage simply
    contains no recognizable date/time expressions -- not an error. When the
    passage's language is known, narrowing `options.languages` to it (e.g.
    ["en"]) gives tighter, more reliable match boundaries than the default
    multi-language shortlist: with several languages active at once,
    dateparser's span-finding can pick a shorter or looser boundary than the
    single-language parser would, since it is choosing among more competing
    candidate spans.
    """
    try:
        text = check_text(text=input.text, field="text")
        settings, languages, _ = build_settings(input.base_time, input.options)
    except DPError as exc:
        return FoundDateTimeExpressions(error={"code": exc.code, "message": exc.message})

    try:
        from dateparser.search import search_dates

        raw = search_dates(text, languages=languages, settings=settings)
    except Exception as exc:
        return FoundDateTimeExpressions(
            error={"code": "INTERNAL", "message": f"the request could not be processed: {exc}"}
        )

    if not raw:
        return FoundDateTimeExpressions()

    located = locate_matches(text, raw)
    matches = [
        DateTimeMatch(text=matched_text, start_index=start, datetime=dt.isoformat())
        for matched_text, start, dt in located
    ]
    return FoundDateTimeExpressions(matches=matches)
