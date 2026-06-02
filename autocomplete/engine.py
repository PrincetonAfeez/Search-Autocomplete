""" Autocomplete engine. """

from __future__ import annotations

from collections.abc import Iterable

from .constants import MAX_TERM_LENGTH
from .normalizer import normalize
from .suggestion import Suggestion
from .trie import Trie


class AutocompleteEngine:
    def __init__(
        self,
        trie: Trie | None = None,
        *,
        min_prefix_length: int = 2,
        default_limit: int = 10,
    ) -> None:
        if min_prefix_length < 0:
            raise ValueError("min_prefix_length must be greater than or equal to 0")
        if default_limit < 1:
            raise ValueError("default_limit must be greater than 0")

        self.trie = trie or Trie()
        self.min_prefix_length = min_prefix_length
        self.default_limit = default_limit

    def contains(self, word: str) -> bool:
        return self.trie.contains(word[:MAX_TERM_LENGTH])

    def normalize_query(self, prefix: str) -> str:
        return normalize(prefix[:MAX_TERM_LENGTH])

    def is_too_short(self, prefix: str) -> bool:
        length = len(self.normalize_query(prefix))
        return 0 < length < self.min_prefix_length

    def suggest(self, prefix: str, k: int | None = None) -> list[Suggestion]:
        """Return ranked suggestions for ``prefix``.

        ``k=0`` (or any non-positive limit) returns an empty list without error.
        The constructor rejects ``default_limit=0``; only per-call ``k`` may be zero.
        """
        limit = self.default_limit if k is None else k

        if limit <= 0:
            return []

        bounded = prefix[:MAX_TERM_LENGTH]
        normalized = self.normalize_query(bounded)
        if not normalized or len(normalized) < self.min_prefix_length:
            return []

        return self.trie.collect_top_k(bounded, limit)

    def rebuild(self, words: Iterable[tuple[str, int]]) -> None:
        trie = Trie()
        for word, weight in words:
            trie.insert(word, weight)
        self.trie = trie
