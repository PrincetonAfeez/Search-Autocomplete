""" Tests for the Word model. """

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from autocomplete.constants import MAX_WEIGHT
from corpus.loader import rebuild_engine
from corpus.models import Word


@pytest.mark.django_db
def test_word_generates_normalized_text():
    word = Word.objects.create(text="  Python  ", weight=100)

    assert word.text == "Python"
    assert word.normalized_text == "python"


@pytest.mark.django_db
def test_word_rejects_duplicate_normalized_text():
    Word.objects.create(text="Python", weight=100)

    with pytest.raises(ValidationError):
        Word.objects.create(text="PYTHON", weight=90)


@pytest.mark.django_db
def test_word_rejects_blank_text():
    with pytest.raises(ValidationError):
        Word.objects.create(text="   ", weight=1)


@pytest.mark.django_db
def test_word_accepts_zero_weight():
    word = Word.objects.create(text="Zero", weight=0)

    assert word.weight == 0
    assert Word.objects.get(normalized_text="zero").weight == 0


@pytest.mark.django_db
def test_word_rejects_text_exceeding_max_length():
    with pytest.raises(ValidationError):
        Word.objects.create(text="a" * 256, weight=1)


@pytest.mark.django_db
def test_word_rejects_negative_weight():
    with pytest.raises(ValidationError):
        Word.objects.create(text="Bad", weight=-1)


@pytest.mark.django_db
def test_word_accepts_max_weight():
    word = Word.objects.create(text="Heavy", weight=MAX_WEIGHT)

    assert word.weight == MAX_WEIGHT


@pytest.mark.django_db
def test_word_rejects_weight_above_max():
    with pytest.raises(ValidationError):
        Word.objects.create(text="TooHeavy", weight=MAX_WEIGHT + 1)


@pytest.mark.django_db
def test_word_database_constraint_rejects_weight_above_max():
    with pytest.raises(IntegrityError):
        Word.objects.bulk_create(
            [
                Word(
                    text="TooHeavy",
                    normalized_text="tooheavy",
                    weight=MAX_WEIGHT + 1,
                )
            ]
        )


@pytest.mark.django_db
def test_rebuild_engine_accepts_max_weight_word():
    Word.objects.create(text="Heavy", weight=MAX_WEIGHT)

    engine = rebuild_engine()

    assert [suggestion.word for suggestion in engine.suggest("he")] == ["Heavy"]


@pytest.mark.django_db
def test_word_rejects_normalized_text_exceeding_max_length():
    # Each ß casefolds to "ss", expanding normalized length beyond display length.
    with pytest.raises(ValidationError):
        Word.objects.create(text="ß" * 128, weight=1)


@pytest.mark.django_db
def test_deactivating_word_via_save_excludes_from_suggestions():
    from corpus.loader import get_engine

    word = Word.objects.create(text="Python", weight=100)
    assert [s.word for s in get_engine().suggest("py")] == ["Python"]

    word.is_active = False
    word.save()

    assert get_engine().suggest("py") == []


@pytest.mark.django_db
def test_word_str_includes_text_and_weight():
    word = Word.objects.create(text="Python", weight=100)

    assert str(word) == "Python (100)"


@pytest.mark.django_db
def test_queryset_update_zero_rows_does_not_clear_engine(monkeypatch):
    from corpus.loader import get_engine
    import corpus.loader as loader_module

    Word.objects.create(text="Python", weight=100)
    get_engine()
    calls = []
    monkeypatch.setattr(loader_module, "clear_engine", lambda: calls.append(1))

    Word.objects.filter(normalized_text="missing").update(weight=5)

    assert calls == []


@pytest.mark.django_db
def test_bulk_create_empty_list_does_not_clear_engine(monkeypatch):
    from corpus.loader import get_engine
    import corpus.loader as loader_module

    get_engine()
    calls = []
    monkeypatch.setattr(loader_module, "clear_engine", lambda: calls.append(1))

    Word.objects.bulk_create([])

    assert calls == []


@pytest.mark.django_db
def test_bulk_update_returns_updated_count():
    word = Word.objects.create(text="Python", weight=100)
    word.weight = 200

    updated = Word.objects.bulk_update([word], ["weight"])

    assert updated == 1
    assert Word.objects.get(normalized_text="python").weight == 200


@pytest.mark.django_db
def test_bulk_update_empty_list_does_not_clear_engine(monkeypatch):
    from corpus.loader import get_engine
    import corpus.loader as loader_module

    get_engine()
    calls = []
    monkeypatch.setattr(loader_module, "clear_engine", lambda: calls.append(1))

    Word.objects.bulk_update([], ["weight"])

    assert calls == []
