""" Tests for the loader. """

import threading

import pytest

from corpus.loader import clear_engine, get_engine, rebuild_engine
from corpus.models import Word


@pytest.mark.django_db
def test_get_engine_lazily_builds_singleton():
    Word.objects.create(text="Python", weight=100)

    first = get_engine()
    second = get_engine()

    assert first is second
    assert [suggestion.word for suggestion in first.suggest("py")] == ["Python"]


@pytest.mark.django_db
def test_rebuild_engine_replaces_singleton_and_skips_inactive_words():
    Word.objects.create(text="Python", weight=100)
    first = get_engine()

    Word.objects.create(text="Pytest", weight=80, is_active=False)
    Word.objects.create(text="Pyramid", weight=70)
    rebuilt = rebuild_engine()

    assert rebuilt is not first
    assert [suggestion.word for suggestion in rebuilt.suggest("py")] == [
        "Python",
        "Pyramid",
    ]


@pytest.mark.django_db
def test_post_save_signal_invalidates_engine():
    Word.objects.create(text="Python", weight=100)

    first = get_engine()
    Word.objects.create(text="Pytest", weight=80)

    rebuilt = get_engine()
    assert rebuilt is not first
    assert {s.word for s in rebuilt.suggest("py")} == {"Python", "Pytest"}


@pytest.mark.django_db
def test_post_delete_signal_invalidates_engine():
    word = Word.objects.create(text="Python", weight=100)
    first = get_engine()
    assert [s.word for s in first.suggest("py")] == ["Python"]

    word.delete()

    rebuilt = get_engine()
    assert rebuilt is not first
    assert rebuilt.suggest("py") == []


@pytest.mark.django_db(transaction=True)
def test_get_engine_is_thread_safe():
    Word.objects.create(text="Python", weight=100)

    results: list[object] = []
    barrier = threading.Barrier(8)

    def worker() -> None:
        barrier.wait()
        results.append(get_engine())

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 8
    first = results[0]
    assert all(engine is first for engine in results)


@pytest.mark.django_db(transaction=True)
def test_rollback_after_failed_save_rebuilds_from_database():
    from django.db import IntegrityError, transaction

    Word.objects.create(text="Python", weight=100)
    first = get_engine()
    assert [s.word for s in first.suggest("py")] == ["Python"]

    try:
        with transaction.atomic():
            Word.objects.create(text="Pytest", weight=80)
            raise IntegrityError("forced rollback")
    except IntegrityError:
        pass

    rebuilt = get_engine()
    assert rebuilt is not first
    assert {s.word for s in rebuilt.suggest("py")} == {"Python"}


@pytest.mark.django_db
def test_queryset_update_invalidates_engine():
    Word.objects.create(text="Python", weight=100)
    Word.objects.create(text="Pyramid", weight=70)

    first = get_engine()
    assert {s.word for s in first.suggest("py")} == {"Python", "Pyramid"}

    Word.objects.filter(normalized_text="pyramid").update(is_active=False)

    rebuilt = get_engine()
    assert rebuilt is not first
    assert [s.word for s in rebuilt.suggest("py")] == ["Python"]


@pytest.mark.django_db
def test_build_engine_respects_autocomplete_settings(settings):
    settings.AUTOCOMPLETE_MIN_PREFIX = 3
    settings.AUTOCOMPLETE_LIMIT = 1

    Word.objects.create(text="Python", weight=100)
    Word.objects.create(text="Pyramid", weight=90)

    engine = rebuild_engine()

    assert engine.suggest("py") == []
    assert len(engine.suggest("pyt")) == 1
    assert [s.word for s in engine.suggest("pyt")] == ["Python"]


@pytest.mark.django_db
def test_bulk_create_invalidates_engine():
    first = get_engine()
    assert first.suggest("py") == []

    Word.objects.bulk_create(
        [Word(text="Python", normalized_text="python", weight=100, is_active=True)]
    )

    rebuilt = get_engine()
    assert rebuilt is not first
    assert [s.word for s in rebuilt.suggest("py")] == ["Python"]


@pytest.mark.django_db
def test_bulk_update_invalidates_engine():
    word = Word.objects.create(text="Python", weight=100)
    Word.objects.create(text="Pyramid", weight=70)

    first = get_engine()
    assert {s.word for s in first.suggest("py")} == {"Python", "Pyramid"}

    word.is_active = False
    Word.objects.bulk_update([word], ["is_active"])

    rebuilt = get_engine()
    assert rebuilt is not first
    assert [s.word for s in rebuilt.suggest("py")] == ["Pyramid"]


@pytest.mark.django_db
def test_clear_engine_is_idempotent():
    Word.objects.create(text="Python", weight=100)
    first = get_engine()

    clear_engine()
    clear_engine()

    second = get_engine()
    assert second is not first
    assert [s.word for s in second.suggest("py")] == ["Python"]


@pytest.mark.django_db
def test_build_engine_with_empty_database():
    from corpus.loader import build_engine

    engine = build_engine()

    assert engine.suggest("py") == []
    assert len(engine.trie) == 0
