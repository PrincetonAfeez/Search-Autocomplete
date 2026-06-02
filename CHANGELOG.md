# Changelog

## 0.1.0 — Portfolio release

### Core
- Hand-built trie with insert, delete/prune, bounded top-k collection
- Casefold normalization with display-aligned prefix highlighting
- `AutocompleteEngine` with configurable min prefix and top-k limits

### Django integration
- `Word` model with validation and `WordQuerySet` cache invalidation on update/bulk writes
- Lazy process-level engine singleton with signal-based invalidation
- `seed_corpus` and `rebuild_trie` management commands
- Admin activate/deactivate and bulk delete with cache coherence

### Web + CLI
- HTMX search page with keyboard navigation and ARIA combobox pattern
- Optional CLI / `search-autocomplete` console entry point

### Quality
- 85%+ coverage gate, Ruff lint, mypy on core, pip-audit in CI
- Playwright e2e smoke test, hypothesis fuzz tests, performance regression test
- Seven ADRs and supporting docs (architecture, complexity, evaluation, test plan)
