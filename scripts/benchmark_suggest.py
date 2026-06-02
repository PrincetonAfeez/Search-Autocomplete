#!/usr/bin/env python3
"""Benchmark suggest latency for a given prefix and corpus size."""

from __future__ import annotations

import argparse
import statistics
import time

from autocomplete import AutocompleteEngine, Trie


def build_trie(word_count: int) -> Trie:
    trie = Trie()
    for index in range(word_count):
        trie.insert(f"word{index:05d}", weight=index % 100)
    return trie


def benchmark(prefix: str, word_count: int, iterations: int) -> None:
    engine = AutocompleteEngine(build_trie(word_count))
    timings: list[float] = []

    for _ in range(iterations):
        start = time.perf_counter()
        engine.suggest(prefix)
        timings.append(time.perf_counter() - start)

    print(
        f"prefix={prefix!r} corpus={word_count} iterations={iterations} "
        f"mean_ms={statistics.mean(timings) * 1000:.2f} "
        f"p95_ms={sorted(timings)[int(len(timings) * 0.95) - 1] * 1000:.2f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark autocomplete suggest().")
    parser.add_argument("--prefix", default="word1")
    parser.add_argument("--words", type=int, default=5000)
    parser.add_argument("--iterations", type=int, default=50)
    args = parser.parse_args()
    benchmark(args.prefix, args.words, args.iterations)


if __name__ == "__main__":
    main()
