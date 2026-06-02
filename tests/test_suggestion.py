""" Tests for the suggestion. """

from autocomplete import Suggestion


def test_suggestion_is_frozen_and_fields_are_accessible():
    suggestion = Suggestion(
        word="Python",
        normalized_word="python",
        weight=100,
        matched_length=2,
        matched_display_length=2,
    )

    assert suggestion.word == "Python"
    assert suggestion.normalized_word == "python"
    assert suggestion.weight == 100
    assert suggestion.matched_length == 2
    assert suggestion.matched_display_length == 2


def test_suggestion_equality():
    left = Suggestion("A", "a", 1, 1, 1)
    right = Suggestion("A", "a", 1, 1, 1)

    assert left == right
