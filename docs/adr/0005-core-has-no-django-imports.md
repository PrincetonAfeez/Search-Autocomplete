# ADR 0005: Core Has No Django Imports

## Decision

Keep the pure Trie and autocomplete engine independent from Django.

## Reason

The data structure should be reusable, easy to unit-test, and importable without
pulling in the web stack.

## Trade-off

Django needs a small loader layer to adapt database rows into the core engine.
The optional `cli.py` is a Django convenience wrapper (`django.setup()` plus
`corpus.loader`); it is not a standalone trie REPL. The dependency direction is
`cli -> corpus.loader -> autocomplete`, not `cli -> autocomplete` directly.
