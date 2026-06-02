""" Tests for corpus apps. """

import pytest
from django.db.models.signals import post_delete, post_save

from corpus.apps import (
    WORD_INVALIDATE_DELETE_UID,
    WORD_INVALIDATE_SAVE_UID,
    invalidate_engine,
)
from corpus.loader import get_engine
from corpus.models import Word


def _has_receiver(signal, uid):
    for entry in signal.receivers:
        lookup_key = entry[0]
        if isinstance(lookup_key, tuple) and lookup_key and lookup_key[0] == uid:
            return True
    return False


@pytest.mark.django_db
def test_invalidate_engine_receiver_clears_cache():
    Word.objects.create(text="Python", weight=100)
    first = get_engine()
    assert [s.word for s in first.suggest("py")] == ["Python"]

    invalidate_engine()

    rebuilt = get_engine()
    assert rebuilt is not first


def test_corpus_app_registers_save_and_delete_signals():
    assert _has_receiver(post_save, WORD_INVALIDATE_SAVE_UID)
    assert _has_receiver(post_delete, WORD_INVALIDATE_DELETE_UID)
