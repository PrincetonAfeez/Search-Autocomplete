""" Fixtures for the test suite. """

import pytest

from corpus.loader import clear_engine


@pytest.fixture(autouse=True)
def _reset_engine_cache():
    """Reset the lazy engine singleton around every test.

    The engine lives at module scope in `corpus.loader` and pytest-django
    does not reset module globals between tests. Without this fixture, a
    Word created by one test would leak into the next test's engine cache.
    """
    clear_engine()
    yield
    clear_engine()
