""" Tests for the seed_corpus command. """

import pytest
from django.core.management import CommandError, call_command
from django.db.models.signals import post_delete, post_save

from corpus.apps import WORD_INVALIDATE_DELETE_UID, WORD_INVALIDATE_SAVE_UID
from corpus.management.commands.seed_corpus import _signal_quiet
from corpus.models import Word


def _has_receiver(signal, uid):
    # Django stores entries as (lookup_key, receiver, ...). When dispatch_uid is
    # used, lookup_key is (dispatch_uid, sender_id).
    for entry in signal.receivers:
        lookup_key = entry[0]
        if isinstance(lookup_key, tuple) and lookup_key and lookup_key[0] == uid:
            return True
    return False


@pytest.mark.django_db
def test_seed_command_creates_and_updates_words(tmp_path):
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python,100\nPYTHON,120\nPytest,80\nBad,-1\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file))

    assert Word.objects.count() == 2
    assert Word.objects.get(normalized_text="python").text == "PYTHON"
    assert Word.objects.get(normalized_text="python").weight == 120
    assert Word.objects.get(normalized_text="pytest").weight == 80


@pytest.mark.django_db
def test_seed_command_dry_run_does_not_write(tmp_path):
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python,100\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file), dry_run=True)

    assert Word.objects.count() == 0


@pytest.mark.django_db
def test_seed_command_dry_run_reports_create_and_update_counts(tmp_path, capsys):
    Word.objects.create(text="Python", weight=10)
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python,100\nPytest,80\nBad,-1\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file), dry_run=True)

    out = capsys.readouterr().out
    assert "would_create=1" in out
    assert "would_update=1" in out
    assert "invalid=1" in out


@pytest.mark.django_db
def test_seed_command_clear_removes_existing_then_imports(tmp_path):
    Word.objects.create(text="Stale", weight=1)
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python,100\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file), clear=True)

    assert Word.objects.count() == 1
    assert Word.objects.get(normalized_text="python").text == "Python"


@pytest.mark.django_db
def test_seed_command_clear_dry_run_reports_all_as_create(tmp_path, capsys):
    Word.objects.create(text="Python", weight=10)
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python,100\nPytest,80\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file), clear=True, dry_run=True)

    out = capsys.readouterr().out
    # --clear wipes existing rows, so both CSV entries are create candidates.
    assert "would_create=2" in out
    assert "would_update=0" in out
    assert Word.objects.count() == 1  # dry-run must not touch the DB


@pytest.mark.django_db
def test_seed_command_invalidates_engine_cache(tmp_path):
    from corpus.loader import get_engine

    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python,100\n", encoding="utf-8")

    before = get_engine()
    assert before.suggest("py") == []

    call_command("seed_corpus", str(corpus_file))

    after = get_engine()
    assert after is not before
    assert [s.word for s in after.suggest("py")] == ["Python"]


@pytest.mark.django_db
def test_seed_command_reports_missing_file(tmp_path):
    with pytest.raises(CommandError):
        call_command("seed_corpus", str(tmp_path / "missing.csv"))


@pytest.mark.django_db
def test_seed_command_dry_run_reports_duplicate_normalized_keys_in_one_file(tmp_path, capsys):
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python,100\nPYTHON,120\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file), dry_run=True)

    out = capsys.readouterr().out
    assert "would_create=1" in out
    assert "would_update=1" in out


@pytest.mark.django_db
def test_seed_command_preserves_is_active_on_update(tmp_path):
    Word.objects.create(text="Python", weight=10, is_active=False)
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python,100\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file))

    word = Word.objects.get(normalized_text="python")
    assert word.weight == 100
    assert word.is_active is False


@pytest.mark.django_db
def test_seed_command_supports_custom_delimiter(tmp_path):
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python;100\nPytest;80\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file), delimiter=";")

    assert Word.objects.count() == 2


@pytest.mark.django_db
def test_seed_command_rejects_negative_default_weight(tmp_path):
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python\n", encoding="utf-8")

    with pytest.raises(CommandError, match="--default-weight"):
        call_command("seed_corpus", str(corpus_file), default_weight=-1)


@pytest.mark.django_db
def test_seed_command_reports_invalid_utf8(tmp_path):
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_bytes(b"Python,\xff\n")

    with pytest.raises(CommandError, match="not valid UTF-8"):
        call_command("seed_corpus", str(corpus_file))


@pytest.mark.django_db
def test_seed_command_reports_overlong_word(tmp_path, capsys):
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text(f"{'a' * 256},1\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file))

    err = capsys.readouterr().err
    assert "exceeds 255 characters" in err
    assert Word.objects.count() == 0


@pytest.mark.django_db
def test_seed_command_warns_on_duplicate_normalized_keys_in_one_file(tmp_path, capsys):
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python,100\nPYTHON,120\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file))

    err = capsys.readouterr().err
    assert "updates normalized key already seen in file" in err
    assert Word.objects.count() == 1


def test_signal_quiet_restores_signals_after_exception():
    assert _has_receiver(post_save, WORD_INVALIDATE_SAVE_UID)
    assert _has_receiver(post_delete, WORD_INVALIDATE_DELETE_UID)

    with pytest.raises(RuntimeError):
        with _signal_quiet():
            assert not _has_receiver(post_save, WORD_INVALIDATE_SAVE_UID)
            assert not _has_receiver(post_delete, WORD_INVALIDATE_DELETE_UID)
            raise RuntimeError("boom")

    assert _has_receiver(post_save, WORD_INVALIDATE_SAVE_UID)
    assert _has_receiver(post_delete, WORD_INVALIDATE_DELETE_UID)


@pytest.mark.django_db
def test_seed_command_rejects_directory_path(tmp_path):
    with pytest.raises(CommandError, match="not a file"):
        call_command("seed_corpus", str(tmp_path))


@pytest.mark.django_db
def test_seed_command_rejects_default_weight_above_max(tmp_path):
    from autocomplete.constants import MAX_WEIGHT

    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python\n", encoding="utf-8")

    with pytest.raises(CommandError, match="--default-weight"):
        call_command("seed_corpus", str(corpus_file), default_weight=MAX_WEIGHT + 1)


@pytest.mark.django_db
def test_seed_command_reports_three_column_rows(tmp_path, capsys):
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python,100,extra\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file))

    err = capsys.readouterr().err
    assert "expected at most two columns" in err
    assert Word.objects.count() == 0


@pytest.mark.django_db
def test_seed_command_reports_non_integer_weight(tmp_path, capsys):
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python,abc\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file))

    err = capsys.readouterr().err
    assert "weight must be an integer" in err
    assert Word.objects.count() == 0


@pytest.mark.django_db
def test_seed_command_reports_weight_above_max(tmp_path, capsys):
    from autocomplete.constants import MAX_WEIGHT

    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text(f"Python,{MAX_WEIGHT + 1}\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file))

    err = capsys.readouterr().err
    assert "weight must be less than or equal to" in err
    assert Word.objects.count() == 0


@pytest.mark.django_db
def test_seed_command_reports_normalized_length_overflow(tmp_path, capsys):
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text(f"{'ß' * 128},1\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file))

    err = capsys.readouterr().err
    assert "normalized word exceeds" in err
    assert Word.objects.count() == 0


@pytest.mark.django_db
def test_seed_command_uses_default_weight_for_unweighted_rows(tmp_path):
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file), default_weight=42)

    assert Word.objects.get(normalized_text="python").weight == 42


@pytest.mark.django_db
def test_seed_command_skips_blank_rows(tmp_path):
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("\n  ,  \nPython,100\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file))

    assert Word.objects.count() == 1


@pytest.mark.django_db
def test_seed_command_reports_blank_word(tmp_path, capsys):
    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("   ,100\nPython,100\n", encoding="utf-8")

    call_command("seed_corpus", str(corpus_file))

    err = capsys.readouterr().err
    assert "word must not be blank" in err
    assert Word.objects.count() == 1


@pytest.mark.django_db
def test_seed_command_reports_malformed_csv(tmp_path, monkeypatch):
    import csv

    corpus_file = tmp_path / "words.csv"
    corpus_file.write_text("Python,100\n", encoding="utf-8")

    def broken_reader(*args, **kwargs):
        raise csv.Error("invalid CSV")

    monkeypatch.setattr(
        "corpus.management.commands.seed_corpus.csv.reader",
        broken_reader,
    )

    with pytest.raises(CommandError, match="not valid CSV"):
        call_command("seed_corpus", str(corpus_file))


def test_seed_command_help_text():
    from corpus.management.commands.seed_corpus import Command

    assert "Seed the Word corpus" in Command.help
