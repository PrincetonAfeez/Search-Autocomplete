# Evaluation summary

## Learning outcomes demonstrated

1. **Data structures** — hand-built trie with insert, delete/prune, and top-k traversal.
2. **Systems layering** — pure Python core + Django adapter + HTMX UI with explicit dependency direction.
3. **Engineering trade-offs** — documented in seven ADRs (singleton, DB source of truth, cache invalidation, security posture).
4. **Quality** — 85%+ line coverage gate, unit/integration/e2e tests, lint and typecheck in CI.

## Approach

The database stores authoritative `Word` rows. A process-level `AutocompleteEngine` rebuilds a trie index on demand. Exact prefix matching uses Unicode casefold; ranking is static weight then alphabetical order on normalized text.

## Trade-offs accepted

- No fuzzy/typo correction (ADR 0003)
- No cross-process cache invalidation (ADR 0006)
- Top-k time O(m) under the matched prefix (ADR 0004, `docs/complexity.md`)
- Localhost-oriented security (ADR 0007)

## What I would do differently with more time

1. **Persistent trie snapshots** — faster cold start without full DB scan.
2. **Unicode NFC normalization** — canonical composed forms before casefold.
3. **Playwright + axe in CI** — automated accessibility regression on every PR.
4. **Bounded top-k without full subtree visit** — weight-indexed trie nodes or auxiliary heap per subtree.

## Self-assessment rubric (target)

| Dimension | Evidence in repo |
| --- | --- |
| Correctness | 89+ pytest cases, hypothesis fuzz on trie |
| Design | ADRs, architecture + sequence diagrams |
| Testing | Coverage gate, e2e smoke, perf benchmark script |
| Documentation | README, troubleshooting, test plan traceability |
| Portfolio | CI badges, CHANGELOG, Makefile/tasks |
