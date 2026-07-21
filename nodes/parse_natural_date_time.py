from gen.messages_pb2 import NaturalDateTimeRequest, ParsedNaturalDateTime
from gen.axiom_context import AxiomContext

from nodes._dp import DPError, build_settings, check_text, resolve


def parse_natural_date_time(ax: AxiomContext, input: NaturalDateTimeRequest) -> ParsedNaturalDateTime:
    """Resolve one natural-language date/time expression into a normalized
    ISO 8601 instant, anchored to `base_time` rather than the wall clock.

    Relative phrases ("3 days ago", "next month") and absolute ones
    ("2026-01-15", "March 1") are both supported, in whichever languages
    `options.languages` selects (or this package's default shortlist).
    `found=false` is a normal negative result -- `text` simply was not
    recognized as a date/time expression -- not an error.
    """
    try:
        text = check_text(input.text, "text")
        settings, languages, _ = build_settings(input.base_time, input.options)
        data = resolve(text, settings, languages)
    except DPError as exc:
        return ParsedNaturalDateTime(error={"code": exc.code, "message": exc.message})
    except Exception as exc:
        # This node runs with no process isolation, so nothing else stops an
        # internal fault reaching the caller as a raw traceback. Reported as
        # ours, not as their input's.
        return ParsedNaturalDateTime(
            error={"code": "INTERNAL", "message": f"the request could not be processed: {exc}"}
        )

    if data.date_obj is None:
        return ParsedNaturalDateTime(found=False)

    return ParsedNaturalDateTime(
        datetime=data.date_obj.isoformat(),
        found=True,
        detected_language=data.locale or "",
        period=data.period or "",
    )
