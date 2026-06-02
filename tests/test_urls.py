""" Tests for URLs. """

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_root_redirects_to_search(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response.url == reverse("search")


@pytest.mark.django_db
def test_suggest_view_accepts_overlong_query_without_error(client):
    from corpus.models import Word

    Word.objects.create(text="Python", weight=100)

    response = client.get(reverse("suggest"), {"q": "py" + ("x" * 300)})

    assert response.status_code == 200
    assert b"No matches found" in response.content


def test_named_urls_resolve():
    assert reverse("search") == "/search/"
    assert reverse("suggest") == "/suggest/"
