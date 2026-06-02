""" Tests for web views. """

import pytest
from django.urls import reverse

from corpus.models import Word


@pytest.mark.django_db
def test_search_page_loads(client):
    response = client.get(reverse("search"))

    assert response.status_code == 200
    assert b"Search Autocomplete" in response.content


@pytest.mark.django_db
def test_suggest_view_returns_ranked_fragment(client):
    Word.objects.create(text="Python", weight=100)
    Word.objects.create(text="Pytest", weight=80)

    response = client.get(reverse("suggest"), {"q": "py"})

    assert response.status_code == 200
    assert response.content.index(b"Python") < response.content.index(b"Pytest")
    assert b"<strong>Py</strong>thon" in response.content


@pytest.mark.django_db
def test_suggest_view_renders_too_short_and_no_match_states(client):
    Word.objects.create(text="Python", weight=100)

    too_short = client.get(reverse("suggest"), {"q": "p"})
    no_match = client.get(reverse("suggest"), {"q": "zz"})

    assert b"Keep typing" in too_short.content
    assert b"No matches found" in no_match.content


@pytest.mark.django_db
def test_suggest_view_blank_and_whitespace_query_renders_nothing(client):
    Word.objects.create(text="Python", weight=100)

    blank = client.get(reverse("suggest"), {"q": ""})
    whitespace = client.get(reverse("suggest"), {"q": "   "})

    assert b"No matches found" not in blank.content
    assert b"Keep typing" not in blank.content
    assert b"No matches found" not in whitespace.content
    assert b"Keep typing" not in whitespace.content


@pytest.mark.django_db
def test_suggest_view_highlights_casefold_expansion_correctly(client):
    Word.objects.create(text="Straße", weight=10)

    response = client.get(reverse("suggest"), {"q": "stras"})

    # "stras" lands inside the ß expansion; highlight rounds down to "Stra".
    assert b"<strong>Stra</strong>" in response.content


@pytest.mark.django_db
def test_suggest_view_sets_no_store_cache_control(client):
    Word.objects.create(text="Python", weight=100)

    response = client.get(reverse("suggest"), {"q": "py"})

    assert response["Cache-Control"] == "no-store"


@pytest.mark.django_db
def test_suggest_view_rejects_post(client):
    response = client.post(reverse("suggest"), {"q": "py"})

    assert response.status_code == 405


@pytest.mark.django_db
def test_search_view_rejects_post(client):
    response = client.post(reverse("search"))

    assert response.status_code == 405


@pytest.mark.django_db
def test_search_page_includes_autocomplete_assets(client):
    response = client.get(reverse("search"))

    assert b"autocomplete.js" in response.content
    assert b"hx-get" in response.content


@pytest.mark.django_db
def test_suggest_view_respects_limit_from_settings(client, settings):
    settings.AUTOCOMPLETE_LIMIT = 1
    Word.objects.create(text="Python", weight=100)
    Word.objects.create(text="Pytest", weight=80)

    response = client.get(reverse("suggest"), {"q": "py"})

    assert response.content.count(b"<li") == 1
