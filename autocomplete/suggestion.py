""" Suggestion module. """

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Suggestion:
    word: str
    normalized_word: str
    weight: int
    matched_length: int
    matched_display_length: int
