from gen.messages_pb2 import PhraseLanguageRequest, DetectedPhraseLanguage
from gen.axiom_context import AxiomContext

from nodes._dp import DPError, check_text, resolve, validate_languages


def detect_phrase_language(ax: AxiomContext, input: PhraseLanguageRequest) -> DetectedPhraseLanguage:
    """Identify which language a date/time phrase is written in (e.g.
    "il y a 2 heures" -> "fr"), independent of resolving it to an instant.

    `recognized=false` is a normal negative result -- no candidate language's
    date/time patterns matched `text` -- not an error.
    """
    try:
        text = check_text(input.text, "text")
        languages = validate_languages(
            list(input.candidate_languages), "candidate_languages"
        )
        data = resolve(text, settings={}, languages=languages)
    except DPError as exc:
        return DetectedPhraseLanguage(error={"code": exc.code, "message": exc.message})
    except Exception as exc:
        return DetectedPhraseLanguage(
            error={"code": "INTERNAL", "message": f"the request could not be processed: {exc}"}
        )

    if not data.locale:
        return DetectedPhraseLanguage(recognized=False)
    return DetectedPhraseLanguage(language=data.locale, recognized=True)
