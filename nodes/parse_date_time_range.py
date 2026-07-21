from gen.messages_pb2 import DateTimeRangeRequest, ParsedDateTimeRange
from gen.axiom_context import AxiomContext

from nodes._dp import DPError, build_settings, check_text, resolve


def parse_date_time_range(ax: AxiomContext, input: DateTimeRangeRequest) -> ParsedDateTimeRange:
    """Resolve the two ends of a date/time range from independent
    natural-language expressions (e.g. start_text="March 1",
    end_text="March 5"), both anchored to the same `base_time`.

    Each end is parsed on its own -- dateparser has no native "range" concept,
    so this composes two ordinary resolutions rather than inventing a
    delimiter-splitting heuristic of its own. `ordered` is true only when
    both ends were found and start <= end; a reversed or partial pair is a
    normal outcome (`error` stays empty), not an error -- the caller decides
    how to treat it.
    """
    try:
        start_text = check_text(input.start_text, "start_text")
        end_text = check_text(input.end_text, "end_text")
        settings, languages, _ = build_settings(input.base_time, input.options)
        start_data = resolve(start_text, settings, languages)
        end_data = resolve(end_text, settings, languages)
    except DPError as exc:
        return ParsedDateTimeRange(error={"code": exc.code, "message": exc.message})
    except Exception as exc:
        return ParsedDateTimeRange(
            error={"code": "INTERNAL", "message": f"the request could not be processed: {exc}"}
        )

    start_found = start_data.date_obj is not None
    end_found = end_data.date_obj is not None
    ordered = start_found and end_found and start_data.date_obj <= end_data.date_obj

    return ParsedDateTimeRange(
        start_datetime=start_data.date_obj.isoformat() if start_found else "",
        end_datetime=end_data.date_obj.isoformat() if end_found else "",
        start_found=start_found,
        end_found=end_found,
        ordered=ordered,
    )
