# dateparse-tools

Composable [Axiom](https://axiomide.com) nodes for natural-language date/time
parsing, wrapping the BSD-3-Clause [dateparser](https://github.com/scrapinghub/dateparser)
library. Built for the Axiom marketplace under the `christiangeorgelucas` handle.

Every relative expression ("3 days ago", "next month") resolves against a
**caller-supplied reference instant** (`base_time`), never the wall clock, so
every node is deterministic and reproducible across runs and machines.

## Use it from your agent or app

Every node in this package is a **live, auto-scaling API endpoint** on the
[Axiom](https://axiomide.com) marketplace — call it from an AI agent or your own
code, with nothing to self-host.

**📦 See it on the marketplace:**
https://dev.axiomide.com/marketplace/christiangeorgelucas/dateparse-tools@0.1.1

**Hook it up to an AI agent (MCP).** Add Axiom's hosted MCP server to any MCP
client and every node becomes a typed tool your agent can call — search the
catalog, inspect a schema, and invoke it directly.

```bash
# Claude Code
claude mcp add --transport http axiom https://api.axiomide.com/mcp \
  --header "Authorization: Bearer $AXIOM_API_KEY"
```

Claude Desktop, Cursor, or any config-based client:

```json
{
  "mcpServers": {
    "axiom": {
      "type": "http",
      "url": "https://api.axiomide.com/mcp",
      "headers": { "Authorization": "Bearer YOUR_AXIOM_API_KEY" }
    }
  }
}
```

**Call it from the CLI.**

```bash
axiom invoke christiangeorgelucas/dateparse-tools/ParseNaturalDateTime --input '{ ... }'
```

**Call it over HTTP.**

```bash
curl -X POST https://api.axiomide.com/invocations/v1/nodes/christiangeorgelucas/dateparse-tools/0.1.1/ParseNaturalDateTime \
  -H "Authorization: Bearer $AXIOM_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{ ... }'
```

> Input/output schema for each node is on the marketplace page above, or via
> `axiom inspect node christiangeorgelucas/dateparse-tools/ParseNaturalDateTime`.

### Get started free

Install the CLI:

```bash
# macOS / Linux — Homebrew
brew install axiomide/tap/axiom

# macOS / Linux — install script
curl -fsSL https://raw.githubusercontent.com/AxiomIDE/axiom-releases/main/install.sh | sh
```

**Windows:** download the `windows/amd64` `.zip` from the
[releases page](https://github.com/AxiomIDE/axiom-releases/releases), unzip it,
and put `axiom.exe` on your `PATH`.

Then `axiom version` to verify, `axiom login` (GitHub or Google) to authenticate,
and create an API key under **Console → API Keys**. Docs and sign-up at
**[axiomide.com](https://axiomide.com)**.

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
