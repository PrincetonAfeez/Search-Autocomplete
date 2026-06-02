""" Tests for package exports. """

import autocomplete


def test_public_exports_are_importable():
    assert autocomplete.AutocompleteEngine is not None
    assert autocomplete.Suggestion is not None
    assert autocomplete.Trie is not None
    assert autocomplete.TrieNode is not None
    assert callable(autocomplete.normalize)
    assert callable(autocomplete.display_match_length)


def test_all_matches_exported_names():
    assert set(autocomplete.__all__) == {
        "AutocompleteEngine",
        "Suggestion",
        "Trie",
        "TrieNode",
        "display_match_length",
        "normalize",
    }
