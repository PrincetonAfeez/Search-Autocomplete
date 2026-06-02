""" Corpus loader. """

from __future__ import annotations

from threading import Lock

from autocomplete import AutocompleteEngine, Trie

_engine: AutocompleteEngine | None = None
_engine_lock = Lock()


def build_engine() -> AutocompleteEngine:
    from django.conf import settings

    from .models import Word

    trie = Trie()
    rows = Word.objects.filter(is_active=True).values_list("text", "weight").iterator()
    for text, weight in rows:
        trie.insert(text, weight)
    return AutocompleteEngine(
        trie,
        min_prefix_length=settings.AUTOCOMPLETE_MIN_PREFIX,
        default_limit=settings.AUTOCOMPLETE_LIMIT,
    )


def get_engine() -> AutocompleteEngine:
    global _engine

    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = build_engine()
    return _engine


def rebuild_engine() -> AutocompleteEngine:
    global _engine

    with _engine_lock:
        _engine = build_engine()
    return _engine


def clear_engine() -> None:
    global _engine

    with _engine_lock:
        _engine = None
