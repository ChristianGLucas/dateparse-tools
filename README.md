# dateparse-tools

Composable [Axiom](https://axiomide.com) nodes for natural-language date/time
parsing, wrapping the BSD-3-Clause [dateparser](https://github.com/scrapinghub/dateparser)
library. Built for the Axiom marketplace under the `christiangeorgelucas` handle.

Every relative expression ("3 days ago", "next month") resolves against a
**caller-supplied reference instant** (`base_time`), never the wall clock, so
every node is deterministic and reproducible across runs and machines.

## Nodes

- **ParseNaturalDateTime** — resolve one natural-language date/time
  expression (absolute or relative) into a normalized ISO 8601 instant.
- **DetectPhraseLanguage** — identify which language a date/time phrase is
  written in, independent of resolving it to an instant.
- **SearchDateTimeExpressions** — find every date/time expression embedded
  in a longer passage of free text, with its position and resolved value.
- **ParseDateTimeRange** — resolve the two ends of a date/time range from
  independent natural-language expressions, anchored to the same reference
  instant.
- **ListSupportedLanguages** — list the language codes dateparser's bundled
  locale data recognizes.

## Design notes

- **Bounded default language search.** With no `languages` filter, dateparser
  tries every one of its ~200 bundled locales before giving up on unparseable
  text — measured at tens to hundreds of milliseconds per call. Every node
  here defaults to a compact ~18-language shortlist instead, and accepts an
  explicit `languages` override to widen or narrow it.
- **Deterministic timezone handling.** dateparser's own default `TIMEZONE`
  setting is `"local"` (the deploying host's system zone), which would make
  timezone-aware output depend on which machine answered the request. This
  package never leaves that default in play — output is either left naive
  (matching a naive `base_time`) or pinned to an explicit zone ("UTC", or the
  caller's `assume_timezone`).
- **Offline and stateless.** dateparser bundles its own language data; no
  network calls, no persistence.
- **Size and resource limits are the platform's job**, not this package's —
  nodes here do no request/response size or batch-count enforcement of
  their own.

## License

MIT. See `LICENSE`.
