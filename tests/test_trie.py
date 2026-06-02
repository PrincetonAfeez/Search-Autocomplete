""" Tests for the trie. """

import pytest

from autocomplete import Trie


def test_empty_trie_contains_nothing():
    trie = Trie()

    assert len(trie) == 0
    assert not trie.contains("python")
    assert not trie.starts_with("py")
    assert not trie.starts_with("")


def test_starts_with_empty_prefix_returns_true_when_non_empty():
    trie = Trie()
    trie.insert("python")

    assert trie.starts_with("")


def test_insert_contains_starts_with_and_collect():
    trie = Trie()
    trie.insert("Python", weight=100)
    trie.insert("Pytest", weight=80)

    assert len(trie) == 2
    assert trie.contains("python")
    assert trie.contains("PYTEST")
    assert not trie.contains("Py")
    assert trie.starts_with("py")

    suggestions = list(trie.collect("PY"))
    assert {suggestion.word for suggestion in suggestions} == {"Python", "Pytest"}
    assert suggestions[0].matched_length == 2
    assert suggestions[0].matched_display_length == 2


def test_collect_casefold_expansion_yields_display_aligned_length():
    trie = Trie()
    trie.insert("Straße", weight=10)

    suggestions = list(trie.collect("stras"))

    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert suggestion.matched_length == 5
    # "stras" lands inside the ß expansion ('ss') so display length rounds down.
    assert suggestion.matched_display_length == 4
    assert suggestion.word[: suggestion.matched_display_length] == "Stra"


def test_duplicate_normalized_insert_updates_existing_word():
    trie = Trie()
    trie.insert("Python", weight=10)
    trie.insert("PYTHON", weight=99)

    suggestions = list(trie.collect("py"))

    assert len(trie) == 1
    assert suggestions[0].word == "PYTHON"
    assert suggestions[0].weight == 99


def test_insert_rejects_invalid_words_and_weights():
    trie = Trie()

    with pytest.raises(ValueError):
        trie.insert("   ")

    with pytest.raises(ValueError):
        trie.insert("Python", weight=-1)

    with pytest.raises(ValueError):
        trie.insert("a" * 256)


def test_insert_rejects_overlong_normalized_word():
    trie = Trie()

    with pytest.raises(ValueError, match="normalized word exceeds"):
        trie.insert("ß" * 128)


def test_delete_leaf_word():
    trie = Trie()
    trie.insert("car")
    trie.insert("card")

    assert trie.delete("card")
    assert len(trie) == 1
    assert trie.contains("car")
    assert not trie.contains("card")


def test_delete_word_that_is_prefix_of_another_word():
    trie = Trie()
    trie.insert("car")
    trie.insert("card")

    assert trie.delete("car")
    assert not trie.contains("car")
    assert trie.contains("card")
    assert trie.starts_with("car")


def test_delete_shared_prefix_word_preserves_siblings():
    trie = Trie()
    trie.insert("car")
    trie.insert("card")
    trie.insert("care")

    assert trie.delete("card")
    assert trie.contains("car")
    assert trie.contains("care")
    assert not trie.contains("card")


def test_delete_missing_word_returns_false():
    trie = Trie()
    trie.insert("car")

    assert not trie.delete("cat")
    assert len(trie) == 1


def test_delete_prefix_that_is_not_a_word_returns_false():
    trie = Trie()
    trie.insert("car")

    assert not trie.delete("ca")
    assert len(trie) == 1


def test_delete_from_empty_trie_and_empty_input_return_false():
    trie = Trie()

    assert not trie.delete("anything")
    assert not trie.delete("")


def test_collect_returns_nothing_for_unknown_prefix():
    trie = Trie()
    trie.insert("python")

    assert list(trie.collect("xyz")) == []


def test_collect_top_k_returns_ranked_subset():
    trie = Trie()
    trie.insert("Python", 100)
    trie.insert("Pytest", 80)
    trie.insert("Pyramid", 80)
    trie.insert("Pygame", 70)

    suggestions = trie.collect_top_k("py", 2)

    assert [suggestion.word for suggestion in suggestions] == ["Python", "Pyramid"]


def test_collect_top_k_empty_prefix_returns_empty():
    trie = Trie()
    trie.insert("Python", 1)

    assert trie.collect_top_k("", 5) == []


def test_collect_top_k_truncates_overlong_prefix():
    trie = Trie()
    trie.insert("Python", 100)

    overlong = "py" + ("z" * 500)
    bounded = overlong[:255]

    assert trie.collect_top_k(overlong, 5) == trie.collect_top_k(bounded, 5)


def test_len_tracks_insert_and_delete():
    trie = Trie()
    trie.insert("cat")
    trie.insert("car")

    assert len(trie) == 2

    assert trie.delete("cat")
    assert len(trie) == 1


def test_starts_with_unknown_prefix_returns_false():
    trie = Trie()
    trie.insert("python")

    assert trie.starts_with("java") is False


def test_starts_with_empty_prefix_on_empty_trie_returns_false():
    trie = Trie()

    assert trie.starts_with("") is False


def test_starts_with_existing_prefix_returns_true():
    trie = Trie()
    trie.insert("python")

    assert trie.starts_with("py") is True
    assert trie.starts_with("PYTHON") is True


def test_collect_empty_prefix_yields_all_words():
    trie = Trie()
    trie.insert("alpha")
    trie.insert("beta")

    words = {suggestion.word for suggestion in trie.collect("")}

    assert words == {"alpha", "beta"}


def test_collect_top_k_zero_or_negative_returns_empty():
    trie = Trie()
    trie.insert("python")

    assert trie.collect_top_k("py", 0) == []
    assert trie.collect_top_k("py", -3) == []


def test_collect_top_k_unknown_prefix_returns_empty():
    trie = Trie()
    trie.insert("python")

    assert trie.collect_top_k("zz", 5) == []


def test_insert_strips_display_word():
    trie = Trie()
    trie.insert("  Python  ", weight=5)

    suggestions = list(trie.collect("py"))

    assert suggestions[0].word == "Python"


def test_insert_accepts_max_weight():
    trie = Trie()
    from autocomplete.constants import MAX_WEIGHT

    trie.insert("heavy", weight=MAX_WEIGHT)

    assert list(trie.collect("he"))[0].weight == MAX_WEIGHT


def test_insert_rejects_weight_above_max():
    from autocomplete.constants import MAX_WEIGHT

    trie = Trie()

    with pytest.raises(ValueError, match="weight must be less than or equal to"):
        trie.insert("heavy", weight=MAX_WEIGHT + 1)


def test_collect_top_k_alphabetical_tiebreak():
    trie = Trie()
    trie.insert("Pyramid", 80)
    trie.insert("Pytest", 80)

    words = [s.word for s in trie.collect_top_k("py", 2)]

    assert words == ["Pyramid", "Pytest"]


def test_collect_truncates_overlong_prefix():
    trie = Trie()
    trie.insert("Python", 100)

    overlong = "py" + ("z" * 500)

    assert list(trie.collect(overlong)) == list(trie.collect(overlong[:255]))


def test_contains_rejects_whitespace_only_word():
    trie = Trie()

    assert trie.contains("   ") is False


def test_rank_sort_orders_worst_candidate_correctly():
    from autocomplete.trie import _RankSort

    worse = _RankSort((-1, "zebra"))
    better = _RankSort((-10, "alpha"))

    assert worse < better
