from gen.messages_pb2 import SupportedLanguagesRequest
from nodes.list_supported_languages import list_supported_languages
from nodes.testkit import FakeContext


def run(prefix=""):
    ax = FakeContext()
    return list_supported_languages(ax, SupportedLanguagesRequest(prefix=prefix))


def test_lists_every_supported_language_including_common_ones():
    r = run()
    codes = set(r.languages)
    assert r.count == len(r.languages) == len(codes)
    # dateparser's bundled CLDR-derived data covers 200+ locales.
    assert r.count > 150
    for code in ("en", "fr", "de", "es", "zh", "ar"):
        assert code in codes


def test_prefix_filters_the_catalog():
    r = run(prefix="en")
    assert list(r.languages) == ["en"]
    assert r.count == 1


def test_prefix_with_no_matches_returns_an_empty_list_not_an_error():
    r = run(prefix="zzz-nonexistent")
    assert list(r.languages) == []
    assert r.count == 0


def test_repeated_invocation_is_deterministic():
    a = run()
    b = run()
    assert list(a.languages) == list(b.languages)
