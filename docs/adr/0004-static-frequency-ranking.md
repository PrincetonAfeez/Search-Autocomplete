# ADR 0004: Static Frequency Ranking

## Decision

Rank suggestions by static corpus weight, then alphabetically by normalized word.

## Reason

The behavior is deterministic and clear enough to teach top-K ranking.

## Trade-off

The app does not learn from user behavior.

Top-K selection uses a bounded heap during trie traversal (`Trie.collect_top_k`),
keeping memory at O(k). Time remains O(m) where m is the number of nodes under
the matched prefix, because ranking requires visiting every candidate unless
additional index metadata is maintained.
