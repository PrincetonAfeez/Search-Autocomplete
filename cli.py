""" Command-line interface for the search autocomplete application. """

from __future__ import annotations

import argparse
import os
import sys
from importlib.metadata import PackageNotFoundError, version


def _ensure_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django

    django.setup()


def _resolve_version() -> str:
    try:
        return version("search-autocomplete")
    except PackageNotFoundError:
        # Running from a source checkout without `pip install -e .`.
        return "0.0.0+source"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search Autocomplete REPL.")
    parser.add_argument(
        "--version",
        action="version",
        version=f"search-autocomplete {_resolve_version()}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum suggestions per prefix. Defaults to the engine setting.",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild the engine from the database before starting the REPL.",
    )
    parser.add_argument(
        "prefix",
        nargs="?",
        help="Optional single prefix. When given, prints suggestions and exits.",
    )
    return parser.parse_args(argv)


_CLI_WORD_COL_WIDTH = 20
_CLI_TRUNCATION_MARK = "..."  # ASCII so non-UTF-8 Windows code pages don't choke.


def print_suggestions(engine, prefix: str, limit: int | None) -> None:
    if engine.is_too_short(prefix):
        print("Keep typing")
        return

    suggestions = engine.suggest(prefix) if limit is None else engine.suggest(prefix, k=limit)
    if not suggestions:
        print("No matches")
        return

    for index, suggestion in enumerate(suggestions, start=1):
        word = suggestion.word
        if len(word) > _CLI_WORD_COL_WIDTH:
            word = word[: _CLI_WORD_COL_WIDTH - len(_CLI_TRUNCATION_MARK)] + _CLI_TRUNCATION_MARK
        print(f"{index}. {word:<{_CLI_WORD_COL_WIDTH}} {suggestion.weight}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.limit is not None and args.limit < 1:
        print("error: --limit must be greater than or equal to 1", file=sys.stderr)
        return 2

    _ensure_django()
    from corpus.loader import get_engine, rebuild_engine

    engine = rebuild_engine() if args.rebuild else get_engine()

    if args.prefix:
        print_suggestions(engine, args.prefix, args.limit)
        return 0

    print("Autocomplete CLI. Submit an empty prefix to quit.")
    while True:
        try:
            prefix = input("prefix> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not prefix:
            break

        print_suggestions(engine, prefix, args.limit)

    return 0


if __name__ == "__main__":
    sys.exit(main())
