""" Tests for core guardrails. """

from pathlib import Path

AUTOCOMPLETE_DIR = Path(__file__).resolve().parents[1] / "autocomplete"


def test_autocomplete_package_has_no_django_imports():
    for path in AUTOCOMPLETE_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "django" not in source.lower(), f"{path.name} must not import Django"
