""" Tests for the trie fuzz. """

import random

from hypothesis import given, settings
from hypothesis import strategies as st

from autocomplete import Trie


@settings(max_examples=50, deadline=None)
@given(
    words=st.lists(
        st.from_regex(r"[a-z]{1,8}", fullmatch=True),
        min_size=1,
        max_size=30,
        unique=True,
    )
)
def test_trie_insert_then_suggest_matches_inserted_word(words):
    trie = Trie()
    for index, word in enumerate(words):
        trie.insert(word, weight=index)

    for word in words:
        assert trie.contains(word)
        suggestions = trie.collect_top_k(word[:2] if len(word) >= 2 else word, k=5)
        normalized = {suggestion.normalized_word for suggestion in suggestions}
        assert word.strip().casefold() in normalized or len(word) < 2


@settings(max_examples=30, deadline=None)
@given(
    words=st.lists(
        st.from_regex(r"[a-z]{2,6}", fullmatch=True),
        min_size=1,
        max_size=15,
        unique=True,
    )
)
def test_trie_delete_removes_word(words):
    trie = Trie()
    for word in words:
        trie.insert(word, weight=1)

    target = random.choice(words)
    assert trie.delete(target)
    assert not trie.contains(target)
    assert len(trie) == len(words) - 1
