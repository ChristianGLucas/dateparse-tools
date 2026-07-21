from gen.messages_pb2 import SupportedLanguagesRequest, SupportedLanguageCatalog
from gen.axiom_context import AxiomContext

from nodes._dp import SUPPORTED_LANGUAGES


def list_supported_languages(ax: AxiomContext, input: SupportedLanguagesRequest) -> SupportedLanguageCatalog:
    """List the language codes dateparser's bundled locale data recognizes --
    the valid values for every other node's `languages` /
    `candidate_languages` option -- optionally filtered by prefix.
    """
    prefix = input.prefix or ""
    codes = [code for code in SUPPORTED_LANGUAGES if code.startswith(prefix)]
    return SupportedLanguageCatalog(languages=codes, count=len(codes))
