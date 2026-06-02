""" Tests for constants. """

from autocomplete.constants import MAX_TERM_LENGTH, MAX_WEIGHT


def test_max_term_length_is_255():
    assert MAX_TERM_LENGTH == 255


def test_max_weight_matches_positive_integer_field():
    assert MAX_WEIGHT == 2_147_483_647
