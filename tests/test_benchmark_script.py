""" Tests for the benchmark script. """

import pytest

from scripts import benchmark_suggest


def test_build_trie_inserts_requested_count():
    trie = benchmark_suggest.build_trie(25)

    assert len(trie) == 25


def test_benchmark_runs_without_error(capsys):
    benchmark_suggest.benchmark("word", word_count=50, iterations=3)

    out = capsys.readouterr().out
    assert "prefix='word'" in out
    assert "corpus=50" in out


def test_benchmark_main_with_args(capsys, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["benchmark_suggest", "--prefix", "word0", "--words", "5", "--iterations", "2"],
    )

    benchmark_suggest.main()

    out = capsys.readouterr().out
    assert "prefix='word0'" in out
    assert "corpus=5" in out


def test_benchmark_script_main_entrypoint():
    import subprocess
    import sys
    from pathlib import Path

    result = subprocess.run(
        [sys.executable, str(Path("scripts") / "benchmark_suggest.py"), "--words", "3", "--iterations", "1"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
        check=False,
    )

    assert result.returncode == 0
    assert "corpus=3" in result.stdout
