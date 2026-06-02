# ADR 0001: Process-Level Trie Singleton

## Decision

Hold one autocomplete engine and Trie per Python process.

## Reason

Autocomplete requests should reuse the in-memory index instead of rebuilding the
Trie or querying the database for every keystroke.

## Trade-off

Each process owns its own Trie. In a single-process deployment, writes are
picked up automatically — see
[ADR 0006](0006-engine-cache-invalidation.md) for the signal-based
invalidation. Multi-worker deployments still require a per-worker rebuild or
restart before every worker sees the new data.
