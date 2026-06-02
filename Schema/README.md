# Schema

This folder documents the core schemas and contracts for the Search Autocomplete repository.

The application is a Django + HTMX autocomplete app backed by a hand-built Python trie. The database remains the source of truth for corpus words, while the in-memory trie is rebuilt from active database rows and used to serve prefix suggestions.

## Files

| File | Purpose |
| --- | --- |
| `database_schema.md` | Human-readable database model schema for the `Word` corpus table. |
| `word.schema.json` | JSON Schema representation of a single persisted `Word` record. |
| `suggestion.schema.json` | JSON Schema representation of an internal suggestion/result row. |
| `corpus_seed.schema.json` | JSON Schema for rows accepted by the corpus seed/import workflow. |
| `configuration.schema.json` | JSON Schema for autocomplete-related environment/configuration values. |
| `api_schema.openapi.yaml` | Simple OpenAPI contract for the public web routes. |

## Notes

- `/suggest/` returns an HTMX HTML partial, not JSON.
- Ranking is static: higher weight first, then alphabetically by normalized word.
- Prefix matching is exact and case-insensitive after normalization.
- The default query limit is application-configured, not passed through the public endpoint.
