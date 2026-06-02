""" Normalizer module. """

def normalize(text: str) -> str:
    """Normalize user input and corpus words for lookup."""
    if not isinstance(text, str):
        raise TypeError("text must be str")
    return text.strip().casefold()


def display_match_length(display_word: str, normalized_match_length: int) -> int:
    """Map a normalized-prefix length back to a display-aligned character count.

    `casefold()` can expand characters (ß -> ss, dotless i -> i, fi ligature -> fi).
    Slicing the display word by the normalized length is wrong in those cases. This
    walks the display word and returns how many display characters fit inside the
    requested normalized length, never splitting an expanded character.
    """
    if normalized_match_length <= 0:
        return 0

    consumed = 0
    for index, char in enumerate(display_word):
        char_length = len(char.casefold())
        if consumed + char_length > normalized_match_length:
            return index
        consumed += char_length
        if consumed >= normalized_match_length:
            return index + 1
    return len(display_word)
