""" Tests for the admin interface. """

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from corpus.admin import WordAdmin
from corpus.loader import get_engine
from corpus.models import Word


@pytest.fixture
def word_admin():
    return WordAdmin(Word, AdminSite())


@pytest.fixture
def admin_request():
    request = RequestFactory().get("/admin/")
    request.user = User.objects.create_superuser("admin", "admin@test.com", "pass")
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


@pytest.mark.django_db
def test_admin_deactivate_selected_invalidates_engine(word_admin, admin_request):
    Word.objects.create(text="Python", weight=100)
    first = get_engine()
    assert [s.word for s in first.suggest("py")] == ["Python"]

    queryset = Word.objects.all()
    word_admin.deactivate_selected(admin_request, queryset)

    rebuilt = get_engine()
    assert rebuilt is not first
    assert rebuilt.suggest("py") == []


@pytest.mark.django_db
def test_admin_activate_selected_invalidates_engine(word_admin, admin_request):
    Word.objects.create(text="Python", weight=100, is_active=False)
    first = get_engine()
    assert first.suggest("py") == []

    queryset = Word.objects.all()
    word_admin.activate_selected(admin_request, queryset)

    rebuilt = get_engine()
    assert rebuilt is not first
    assert [s.word for s in rebuilt.suggest("py")] == ["Python"]


@pytest.mark.django_db
def test_admin_bulk_delete_invalidates_engine(word_admin, admin_request):
    Word.objects.create(text="Python", weight=100)
    first = get_engine()
    assert [s.word for s in first.suggest("py")] == ["Python"]

    word_admin.delete_queryset(admin_request, Word.objects.all())

    rebuilt = get_engine()
    assert rebuilt is not first
    assert rebuilt.suggest("py") == []


@pytest.mark.django_db
def test_admin_delete_model_invalidates_engine(word_admin, admin_request):
    word = Word.objects.create(text="Python", weight=100)
    first = get_engine()
    assert [s.word for s in first.suggest("py")] == ["Python"]

    word_admin.delete_model(admin_request, word)

    rebuilt = get_engine()
    assert rebuilt is not first
    assert rebuilt.suggest("py") == []


def test_word_admin_metadata():
    assert WordAdmin.list_display == (
        "text",
        "normalized_text",
        "weight",
        "is_active",
        "updated_at",
    )
    assert WordAdmin.search_fields == ("text", "normalized_text")
    assert "deactivate_selected" in WordAdmin.actions
    assert "activate_selected" in WordAdmin.actions
