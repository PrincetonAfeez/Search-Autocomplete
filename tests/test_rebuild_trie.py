""" Tests for the rebuild_trie command. """

import pytest
from django.core.management import call_command

from corpus.models import Word


@pytest.mark.django_db
def test_rebuild_trie_reports_empty_corpus(capsys):
    call_command("rebuild_trie")

    out = capsys.readouterr().out
    assert "0 active words" in out


@pytest.mark.django_db
def test_rebuild_trie_rebuilds_active_words(capsys):
    Word.objects.create(text="Python", weight=100)
    Word.objects.create(text="Pytest", weight=80, is_active=False)

    call_command("rebuild_trie")

    out = capsys.readouterr().out
    assert "1 active words" in out
