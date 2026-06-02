# Complexity analysis

Let **n** = number of words in the trie, **L** = max word/normalized length (255),
**p** = normalized prefix length, **m** = number of trie nodes under the prefix
(in worst case **m ≤ n**), and **k** = result limit (default 10).

| Operation | Time | Space | Notes |
| --- | --- | --- | --- |
| `Trie.insert(w)` | O(L) | O(L) new nodes worst case | One walk + optional new branch. |
| `Trie.delete(w)` | O(L) | O(L) path stack | Prunes dead branches on unwind. |
| `Trie.contains(w)` | O(L) | O(1) | Exact lookup. |
| `Trie.collect(prefix)` | O(m) | O(m) iterator | Yields every match under prefix. |
| `Trie.collect_top_k(prefix, k)` | O(m) | O(k) | Visits all matches; heap holds k items. |
| `AutocompleteEngine.suggest()` | O(m) | O(k) | Adds normalize + min-prefix checks O(p). |

## Practical guidance

- **Comfortable locally:** tens of thousands of active words; latency stays snappy for prefixes of length ≥ 2.
- **Degrades when:** prefixes are very short (large **m**) or the corpus is huge with dense shared prefixes (e.g. many words starting with `a`).
- **Not optimized for:** megabyte query strings (capped at 255 chars) or multi-worker cache coherence (see [ADR 0006](adr/0006-engine-cache-invalidation.md)).

Run `python scripts/benchmark_suggest.py --words 50000` to measure on your machine.

## Why trie over alternatives?

| Approach | Prefix search | Ranking | Notes |
| --- | --- | --- | --- |
| **Trie (chosen)** | O(L) walk + O(m) collect | Static top-k over matches | Teaching-friendly; predictable memory. |
| **Hash map** | O(n) scan or separate index | Any | No natural prefix grouping. |
| **DB `LIKE 'py%'`** | Index-dependent | SQL `ORDER BY` | Fine at small scale; this project isolates the index in Python. |
| **Search engine** | Inverted index | BM25, etc. | Out of scope for hand-built core. |
