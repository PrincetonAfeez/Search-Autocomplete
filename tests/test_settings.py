""" Tests for settings. """

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.settings import _env_int


def test_env_int_uses_default_when_unset(monkeypatch):
    monkeypatch.delenv("AUTOCOMPLETE_TEST_INT", raising=False)

    assert _env_int("AUTOCOMPLETE_TEST_INT", 10) == 10


def test_env_int_parses_integer(monkeypatch):
    monkeypatch.setenv("AUTOCOMPLETE_TEST_INT", "5")

    assert _env_int("AUTOCOMPLETE_TEST_INT", 10) == 5


def test_env_int_rejects_non_integer(monkeypatch):
    monkeypatch.setenv("AUTOCOMPLETE_TEST_INT", "abc")

    with pytest.raises(ImproperlyConfigured, match="must be an integer"):
        _env_int("AUTOCOMPLETE_TEST_INT", 10)


def test_env_int_rejects_value_below_minimum(monkeypatch):
    monkeypatch.setenv("AUTOCOMPLETE_TEST_INT", "0")

    with pytest.raises(ImproperlyConfigured, match="must be greater than or equal to 1"):
        _env_int("AUTOCOMPLETE_TEST_INT", 10, minimum=1)
