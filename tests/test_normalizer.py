""" Tests for the normalizer. """

import pytest

from autocomplete.normalizer import display_match_length, normalize


def test_normalize_strips_and_casefolds():
    assert normalize("  PyThOn  ") == "python"
    assert normalize("Straße") == "strasse"


def test_normalize_empty_and_whitespace():
    assert normalize("") == ""
    assert normalize("   ") == ""


def test_normalize_rejects_non_string():
    with pytest.raises(TypeError, match="text must be str"):
        normalize(None)  # type: ignore[arg-type]


def test_display_match_length_ascii_passthrough():
    assert display_match_length("Python", 0) == 0
    assert display_match_length("Python", 2) == 2
    assert display_match_length("Python", 6) == 6
    assert display_match_length("Python", 10) == 6


def test_display_match_length_rounds_down_inside_expanded_character():
    # 'ß' casefolds to 'ss' (length 2). Stopping inside that expansion
    # rounds down to before the ß so we never highlight more than typed.
    assert display_match_length("Straße", 4) == 4  # "Stra"
    assert display_match_length("Straße", 5) == 4  # mid-ß -> "Stra"
    assert display_match_length("Straße", 6) == 5  # "Straß"
    assert display_match_length("Straße", 7) == 6  # "Straße"


def test_display_match_length_handles_fi_ligature_expansion():
    # Latin small ligature fi (U+FB01) casefolds to two characters.
    assert display_match_length("\ufb01le", 1) == 0
    assert display_match_length("\ufb01le", 2) == 1
    assert display_match_length("\ufb01le", 3) == 2


def test_display_match_length_zero_returns_zero():
    assert display_match_length("Python", 0) == 0


def test_display_match_length_beyond_word_returns_full_length():
    assert display_match_length("Hi", 100) == 2


def test_normalize_preserves_internal_whitespace():
    assert normalize("  hello world  ") == "hello world"
