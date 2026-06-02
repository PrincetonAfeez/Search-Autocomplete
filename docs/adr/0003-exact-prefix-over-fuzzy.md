# ADR 0003: Exact Prefix Over Fuzzy Search

## Decision

Support exact-prefix matching only.

## Reason

The project is about understanding Tries. Fuzzy matching adds edit-distance and
ranking complexity that belongs in a later project.

## Trade-off

Typos do not return suggestions.
