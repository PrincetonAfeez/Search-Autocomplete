# ADR 0002: DB Source of Truth, Trie Derived Index

## Decision

Store durable words in Django SQLite and build the Trie from active database
rows.

## Reason

The database gives durable editing and validation. The Trie gives fast prefix
lookup.

## Trade-off

The app maintains two representations. The database remains authoritative, and
the Trie is disposable and rebuildable.
