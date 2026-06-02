""" Tests for the CLI. """

import pytest

from cli import _resolve_version, main, parse_args, print_suggestions
from autocomplete import AutocompleteEngine, Trie


def test_print_suggestions_keep_typing(capsys):
    engine = AutocompleteEngine(Trie(), min_prefix_length=2)

    print_suggestions(engine, "p", None)

    assert "Keep typing" in capsys.readouterr().out


def test_print_suggestions_no_matches(capsys):
    engine = AutocompleteEngine(Trie(), min_prefix_length=2)

    print_suggestions(engine, "zz", None)

    assert "No matches" in capsys.readouterr().out


def test_print_suggestions_formats_ranked_rows(capsys):
    trie = Trie()
    trie.insert("Python", 100)
    engine = AutocompleteEngine(trie, min_prefix_length=2)

    print_suggestions(engine, "py", None)

    out = capsys.readouterr().out
    assert "1. Python" in out
    assert "100" in out


def test_print_suggestions_truncates_long_words(capsys):
    trie = Trie()
    trie.insert("X" * 30, 5)
    engine = AutocompleteEngine(trie, min_prefix_length=1)

    print_suggestions(engine, "x", None)

    assert "..." in capsys.readouterr().out


def test_print_suggestions_respects_explicit_limit(capsys):
    trie = Trie()
    trie.insert("Python", 100)
    trie.insert("Pytest", 80)
    engine = AutocompleteEngine(trie, min_prefix_length=2)

    print_suggestions(engine, "py", limit=1)

    out = capsys.readouterr().out
    assert "1." in out
    assert "2." not in out


def test_resolve_version_returns_non_empty_string():
    assert _resolve_version()


def test_resolve_version_source_fallback(monkeypatch):
    from importlib.metadata import PackageNotFoundError

    def raise_not_found(_name):
        raise PackageNotFoundError

    monkeypatch.setattr("cli.version", raise_not_found)

    assert _resolve_version() == "0.0.0+source"


@pytest.mark.django_db
def test_cli_one_shot_prefix_prints_matches(capsys):
    from corpus.models import Word

    Word.objects.create(text="Python", weight=100)

    assert main(["py"]) == 0
    out = capsys.readouterr().out
    assert "Python" in out


@pytest.mark.django_db
def test_cli_one_shot_too_short_prints_keep_typing(capsys):
    from corpus.models import Word

    Word.objects.create(text="Python", weight=100)

    assert main(["p"]) == 0
    out = capsys.readouterr().out
    assert "Keep typing" in out


@pytest.mark.django_db
def test_cli_one_shot_no_match(capsys):
    from corpus.models import Word

    Word.objects.create(text="Python", weight=100)

    assert main(["zz"]) == 0
    out = capsys.readouterr().out
    assert "No matches" in out


@pytest.mark.django_db
def test_cli_rebuild_flag(capsys):
    from corpus.models import Word

    Word.objects.create(text="Python", weight=100)

    assert main(["--rebuild", "py"]) == 0
    assert "Python" in capsys.readouterr().out


def test_cli_invalid_limit_returns_2(capsys):
    assert main(["py", "--limit", "0"]) == 2


def test_cli_bad_flag_exits_with_code_2():
    with pytest.raises(SystemExit) as exc:
        parse_args(["--not-a-flag"])
    assert exc.value.code == 2


def test_cli_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args(["--version"])
    assert exc.value.code == 0


@pytest.mark.django_db
def test_cli_one_shot_respects_limit_flag(capsys):
    from corpus.models import Word

    Word.objects.create(text="Python", weight=100)
    Word.objects.create(text="Pytest", weight=80)
    Word.objects.create(text="Pyramid", weight=70)

    assert main(["py", "--limit", "2"]) == 0
    out = capsys.readouterr().out
    assert "1." in out
    assert "2." in out
    assert "3." not in out


@pytest.mark.django_db
def test_cli_repl_exits_on_empty_prefix(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "")

    assert main([]) == 0
    assert "Autocomplete CLI" in capsys.readouterr().out


@pytest.mark.django_db
def test_cli_repl_exits_on_eof(monkeypatch, capsys):
    def raise_eof(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)

    assert main([]) == 0


@pytest.mark.django_db
def test_cli_repl_processes_prefix_before_exit(monkeypatch, capsys):
    from corpus.models import Word

    Word.objects.create(text="Python", weight=100)
    inputs = iter(["py", ""])

    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    assert main([]) == 0
    out = capsys.readouterr().out
    assert "Python" in out


def test_cli_module_main_entrypoint():
    import subprocess
    import sys
    from pathlib import Path

    result = subprocess.run(
        [sys.executable, "-m", "cli", "--version"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
        check=False,
    )

    assert result.returncode == 0
    assert "search-autocomplete" in result.stdout
