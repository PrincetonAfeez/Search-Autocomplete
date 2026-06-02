""" Tests for the autocomplete engine. """

import pytest

from autocomplete import AutocompleteEngine, Trie


def make_engine():
    trie = Trie()
    trie.insert("Python", 100)
    trie.insert("Pytest", 80)
    trie.insert("Pyramid", 80)
    trie.insert("Pygame", 70)
    return AutocompleteEngine(trie, min_prefix_length=2, default_limit=10)


def test_suggest_returns_ranked_top_k():
    engine = make_engine()

    suggestions = engine.suggest("PY", k=3)

    assert [suggestion.word for suggestion in suggestions] == [
        "Python",
        "Pyramid",
        "Pytest",
    ]


def test_suggest_returns_empty_for_short_no_match_and_zero_k():
    engine = make_engine()

    assert engine.suggest("p") == []
    assert engine.suggest("zz") == []
    assert engine.suggest("py", k=0) == []


def test_suggest_at_min_prefix_length_boundary():
    engine = AutocompleteEngine(Trie(), min_prefix_length=2)
    engine.trie.insert("Python", 1)

    assert engine.suggest("p") == []
    assert [s.word for s in engine.suggest("py")] == ["Python"]


def test_contains_delegates_to_trie():
    engine = make_engine()

    assert engine.contains("python")
    assert not engine.contains("py")


def test_rebuild_replaces_words():
    engine = make_engine()

    engine.rebuild([("Django", 90), ("Database", 70)])

    assert [suggestion.word for suggestion in engine.suggest("da")] == ["Database"]
    assert [suggestion.word for suggestion in engine.suggest("dj")] == ["Django"]


def test_suggest_default_limit_is_ten():
    trie = Trie()
    for index in range(11):
        trie.insert(f"Py{index}", 100 - index)
    engine = AutocompleteEngine(trie, min_prefix_length=2, default_limit=10)

    suggestions = engine.suggest("py")

    assert len(suggestions) == 10


def test_engine_constructor_rejects_invalid_settings():
    with pytest.raises(ValueError, match="min_prefix_length"):
        AutocompleteEngine(Trie(), min_prefix_length=-1)

    with pytest.raises(ValueError, match="default_limit"):
        AutocompleteEngine(Trie(), default_limit=0)


def test_suggest_empty_prefix_returns_empty_even_with_zero_min_length():
    trie = Trie()
    trie.insert("Python", 1)
    engine = AutocompleteEngine(trie, min_prefix_length=0, default_limit=10)

    assert engine.suggest("") == []
    assert engine.suggest("   ") == []


def test_suggest_truncates_overlong_prefix_consistently():
    trie = Trie()
    trie.insert("Python", 100)
    engine = AutocompleteEngine(trie, min_prefix_length=2, default_limit=10)
    calls: list[str] = []
    original = trie.collect_top_k

    def spy(prefix: str, k: int):
        calls.append(prefix)
        return original(prefix, k)

    trie.collect_top_k = spy  # type: ignore[method-assign]
    overlong = "py" + ("z" * 500)

    engine.suggest(overlong)

    assert len(calls) == 1
    assert calls[0] == overlong[:255]
    assert len(calls[0]) == 255


def test_contains_truncates_before_lookup():
    trie = Trie()
    trie.insert("Python", 100)
    engine = AutocompleteEngine(trie)

    assert engine.contains("python")
    assert not engine.contains("python" + ("z" * 500))


def test_normalize_query_strips_and_truncates():
    engine = AutocompleteEngine(Trie())

    assert engine.normalize_query("  Py  ") == "py"
    assert engine.normalize_query("a" * 300) == "a" * 255


def test_is_too_short_for_empty_and_whitespace():
    engine = AutocompleteEngine(Trie(), min_prefix_length=2)

    assert engine.is_too_short("") is False
    assert engine.is_too_short("   ") is False


def test_is_too_short_for_single_character_prefix():
    engine = AutocompleteEngine(Trie(), min_prefix_length=2)

    assert engine.is_too_short("p") is True
    assert engine.is_too_short("py") is False


def test_is_too_short_respects_min_prefix_length_zero():
    engine = AutocompleteEngine(Trie(), min_prefix_length=0)

    assert engine.is_too_short("p") is False


def test_suggest_with_negative_k_returns_empty():
    engine = make_engine()

    assert engine.suggest("py", k=-1) == []


def test_suggest_single_character_when_min_prefix_is_one():
    trie = Trie()
    trie.insert("Python", 100)
    engine = AutocompleteEngine(trie, min_prefix_length=1, default_limit=10)

    assert [s.word for s in engine.suggest("p")] == ["Python"]


def test_suggest_uses_default_limit_when_k_is_none():
    trie = Trie()
    trie.insert("Python", 100)
    engine = AutocompleteEngine(trie, min_prefix_length=2, default_limit=3)

    for index in range(5):
        trie.insert(f"Pyextra{index}", 50 - index)

    assert len(engine.suggest("py")) == 3


def test_rebuild_empty_corpus_clears_suggestions():
    engine = make_engine()

    engine.rebuild([])

    assert engine.suggest("py") == []
    assert len(engine.trie) == 0


def test_engine_default_constructor_builds_empty_trie():
    engine = AutocompleteEngine()

    assert len(engine.trie) == 0
    assert engine.suggest("py") == []


def test_engine_accepts_min_prefix_length_zero():
    engine = AutocompleteEngine(min_prefix_length=0, default_limit=5)

    assert engine.min_prefix_length == 0


def test_suggestion_objects_include_match_metadata():
    engine = make_engine()

    suggestion = engine.suggest("py", k=1)[0]

    assert suggestion.matched_length == 2
    assert suggestion.matched_display_length == 2
    assert suggestion.normalized_word == "python"
