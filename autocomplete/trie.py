""" Trie module. """

from __future__ import annotations

import heapq
from collections.abc import Iterator
from dataclasses import dataclass, field

from .constants import MAX_TERM_LENGTH, MAX_WEIGHT
from .normalizer import display_match_length, normalize
from .suggestion import Suggestion


@dataclass(slots=True)
class TrieNode:
    children: dict[str, TrieNode] = field(default_factory=dict)
    is_word: bool = False
    word: str | None = None
    normalized_word: str | None = None
    weight: int = 0


class _RankSort:
    """Invert rank ordering so ``heap[0]`` tracks the worst kept candidate."""

    __slots__ = ("rank",)

    def __init__(self, rank: tuple[int, str]) -> None:
        self.rank = rank

    def __lt__(self, other: _RankSort) -> bool:
        return self.rank > other.rank


class Trie:
    def __init__(self) -> None:
        self.root = TrieNode()
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def insert(self, word: str, weight: int = 1) -> None:
        display_word = word.strip()
        normalized_word = normalize(word)

        if not normalized_word:
            raise ValueError("word must not be empty")
        if len(display_word) > MAX_TERM_LENGTH:
            raise ValueError(f"word exceeds {MAX_TERM_LENGTH} characters")
        if len(normalized_word) > MAX_TERM_LENGTH:
            raise ValueError(f"normalized word exceeds {MAX_TERM_LENGTH} characters after casefold")
        if weight < 0:
            raise ValueError("weight must be greater than or equal to 0")
        if weight > MAX_WEIGHT:
            raise ValueError(f"weight must be less than or equal to {MAX_WEIGHT}")

        node = self.root
        for char in normalized_word:
            node = node.children.setdefault(char, TrieNode())

        if not node.is_word:
            self._size += 1

        node.is_word = True
        node.word = display_word
        node.normalized_word = normalized_word
        node.weight = weight

    def contains(self, word: str) -> bool:
        node = self._walk(normalize(word))
        return bool(node and node.is_word)

    def starts_with(self, prefix: str) -> bool:
        normalized_prefix = normalize(prefix)
        if not normalized_prefix:
            return self._size > 0
        return self._walk(normalized_prefix) is not None

    def collect(self, prefix: str) -> Iterator[Suggestion]:
        """Yield every word under ``prefix``.

        Callers using ``AutocompleteEngine`` should prefer ``suggest()``; an empty
        prefix yields the entire trie when used directly on ``Trie``.
        """
        normalized_prefix = normalize(prefix[:MAX_TERM_LENGTH])
        node = self._walk(normalized_prefix)
        if node is None:
            return

        yield from self._collect_from(node, matched_length=len(normalized_prefix))

    def collect_top_k(self, prefix: str, k: int) -> list[Suggestion]:
        """Return up to ``k`` suggestions ranked by weight then normalized word."""
        if k <= 0:
            return []

        normalized_prefix = normalize(prefix[:MAX_TERM_LENGTH])
        if not normalized_prefix:
            return []

        node = self._walk(normalized_prefix)
        if node is None:
            return []

        matched_length = len(normalized_prefix)
        heap: list[tuple[_RankSort, int, Suggestion]] = []
        tie_breaker = 0
        stack: list[TrieNode] = [node]

        while stack:
            current = stack.pop()
            if current.is_word and current.word is not None and current.normalized_word is not None:
                suggestion = Suggestion(
                    word=current.word,
                    normalized_word=current.normalized_word,
                    weight=current.weight,
                    matched_length=matched_length,
                    matched_display_length=display_match_length(current.word, matched_length),
                )
                rank = (-current.weight, current.normalized_word)
                entry = (_RankSort(rank), tie_breaker, suggestion)
                tie_breaker += 1
                if len(heap) < k:
                    heapq.heappush(heap, entry)
                elif rank < heap[0][0].rank:
                    heapq.heapreplace(heap, entry)
            stack.extend(current.children.values())

        return [suggestion for _, _, suggestion in sorted(heap, key=lambda entry: entry[0].rank)]

    def delete(self, word: str) -> bool:
        normalized_word = normalize(word)
        if not normalized_word:
            return False

        path: list[tuple[TrieNode, str]] = []
        node = self.root
        for char in normalized_word:
            child = node.children.get(char)
            if child is None:
                return False
            path.append((node, char))
            node = child

        if not node.is_word:
            return False

        node.is_word = False
        node.word = None
        node.normalized_word = None
        node.weight = 0
        self._size -= 1

        # Walk back up pruning nodes that are no longer on a live path.
        for parent, char in reversed(path):
            current = parent.children[char]
            if current.is_word or current.children:
                break
            del parent.children[char]

        return True

    def _walk(self, text: str) -> TrieNode | None:
        node: TrieNode | None = self.root
        for char in text:
            if node is None:
                return None
            node = node.children.get(char)
        return node

    def _collect_from(self, node: TrieNode, matched_length: int) -> Iterator[Suggestion]:
        stack: list[TrieNode] = [node]
        while stack:
            current = stack.pop()
            if current.is_word and current.word is not None and current.normalized_word is not None:
                yield Suggestion(
                    word=current.word,
                    normalized_word=current.normalized_word,
                    weight=current.weight,
                    matched_length=matched_length,
                    matched_display_length=display_match_length(current.word, matched_length),
                )
            stack.extend(current.children.values())
