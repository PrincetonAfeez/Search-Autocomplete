""" Tests for end-to-end (browser-level) Playwright tests. """

import os

# Playwright's pytest plugin runs hooks in an async context; Django test DB
# setup requires this flag when combined with pytest-django live_server.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

import pytest

pytest.importorskip("playwright")
pytest_plugins = ["pytest_playwright"]


@pytest.mark.e2e
@pytest.mark.django_db
def test_search_page_suggest_smoke(live_server, page):
    from corpus.models import Word

    Word.objects.create(text="Python", weight=100)
    Word.objects.create(text="Pyramid", weight=80)

    page.goto(f"{live_server.url}/search/")
    search = page.locator("#search-input")
    search.click()
    search.press_sequentially("py", delay=100)
    page.wait_for_selector(".suggestion-option", timeout=10_000)

    content = page.content()
    assert "Python" in content
    assert content.index("Python") < content.index("Pyramid")
