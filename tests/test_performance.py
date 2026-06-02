""" Tests for performance. """

import time

import pytest

from autocomplete import AutocompleteEngine, Trie


@pytest.mark.perf
def test_suggest_completes_within_time_budget():
    trie = Trie()
    for index in range(2000):
        trie.insert(f"term{index:04d}", weight=index % 50)

    engine = AutocompleteEngine(trie, min_prefix_length=2, default_limit=10)

    start = time.perf_counter()
    results = engine.suggest("term")
    elapsed = time.perf_counter() - start

    assert len(results) == 10
    assert elapsed < 0.5, f"suggest took {elapsed:.3f}s, expected < 0.5s"
