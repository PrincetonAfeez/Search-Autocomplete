""" Seed corpus command. """

from __future__ import annotations

import csv
from contextlib import contextmanager
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.signals import post_delete, post_save

from autocomplete.constants import MAX_TERM_LENGTH, MAX_WEIGHT
from autocomplete.normalizer import normalize
from corpus.apps import (
    WORD_INVALIDATE_DELETE_UID,
    WORD_INVALIDATE_SAVE_UID,
    invalidate_engine,
)
from corpus.loader import clear_engine
from corpus.models import Word


@contextmanager
def _signal_quiet():
    """Detach the per-Word invalidation handlers during a bulk import.

    Each save and delete normally triggers `clear_engine()` via signals; for a
    seed operation (which performs N writes and possibly a bulk delete via
    --clear) that is N pointless lock cycles. Detaching both signals here and
    invalidating once at the end is correct and orders of magnitude cheaper.
    """
    post_save.disconnect(sender=Word, dispatch_uid=WORD_INVALIDATE_SAVE_UID)
    post_delete.disconnect(sender=Word, dispatch_uid=WORD_INVALIDATE_DELETE_UID)
    try:
        yield
    finally:
        post_save.connect(
            invalidate_engine,
            sender=Word,
            dispatch_uid=WORD_INVALIDATE_SAVE_UID,
        )
        post_delete.connect(
            invalidate_engine,
            sender=Word,
            dispatch_uid=WORD_INVALIDATE_DELETE_UID,
        )


class Command(BaseCommand):
    help = "Seed the Word corpus from a text or CSV file."

    def add_arguments(self, parser) -> None:
        parser.add_argument("path", help="Path to a word file. Use 'word' or 'word,weight' rows.")
        parser.add_argument(
            "--clear", action="store_true", help="Clear existing words before import."
        )
        parser.add_argument(
            "--default-weight", type=int, default=1, help="Weight for rows without one."
        )
        parser.add_argument("--delimiter", default=",", help="CSV delimiter. Defaults to comma.")
        parser.add_argument(
            "--dry-run", action="store_true", help="Validate and report without writing."
        )

    def handle(self, *args, **options) -> None:
        path = Path(options["path"])
        default_weight = options["default_weight"]
        delimiter = options["delimiter"]
        dry_run = options["dry_run"]

        if default_weight < 0:
            raise CommandError("--default-weight must be greater than or equal to 0")
        if default_weight > MAX_WEIGHT:
            raise CommandError(f"--default-weight must be less than or equal to {MAX_WEIGHT}")
        if not path.exists():
            raise CommandError(f"corpus file not found: {path}")
        if not path.is_file():
            raise CommandError(f"corpus path is not a file: {path}")

        rows = list(self._read_rows(path, delimiter, default_weight))

        invalid = 0
        for row_number, _word, _weight, error in rows:
            if error:
                invalid += 1
                self.stderr.write(f"line {row_number}: {error}")

        if dry_run:
            if options["clear"]:
                existing: set[str] = set()
            else:
                existing = set(Word.objects.values_list("normalized_text", flat=True))
            would_create = 0
            would_update = 0
            seen_in_file: set[str] = set()

            for _row_number, word, _weight, error in rows:
                if error:
                    continue
                key = normalize(word)
                if key in existing or key in seen_in_file:
                    would_update += 1
                else:
                    would_create += 1
                seen_in_file.add(key)

            self.stdout.write(
                self.style.SUCCESS(
                    "dry run complete: "
                    f"would_create={would_create}, "
                    f"would_update={would_update}, "
                    f"invalid={invalid}"
                )
            )
            return

        created = 0
        updated = 0
        seen_in_file: set[str] = set()

        with transaction.atomic(), _signal_quiet():
            if options["clear"]:
                Word.objects.all().delete()

            for row_number, word, weight, error in rows:
                if error:
                    continue

                normalized = normalize(word)
                if normalized in seen_in_file:
                    self.stderr.write(
                        f"line {row_number}: updates normalized key already seen in file"
                    )
                seen_in_file.add(normalized)

                _obj, was_created = Word.objects.update_or_create(
                    normalized_text=normalized,
                    defaults={"text": word, "weight": weight},
                )
                created += int(was_created)
                updated += int(not was_created)

        clear_engine()

        self.stdout.write(
            self.style.SUCCESS(
                f"seed complete: created={created}, updated={updated}, invalid={invalid}"
            )
        )

    def _read_rows(
        self,
        path: Path,
        delimiter: str,
        default_weight: int,
    ):
        """Stream parsed CSV rows as (row_number, word, weight, error)."""
        try:
            with path.open(newline="", encoding="utf-8") as corpus_file:
                reader = csv.reader(corpus_file, delimiter=delimiter)
                for row_number, row in enumerate(reader, start=1):
                    if not row or all(not cell.strip() for cell in row):
                        continue

                    word = row[0].strip()
                    if not normalize(word):
                        yield (row_number, word, default_weight, "word must not be blank")
                        continue

                    if len(word) > MAX_TERM_LENGTH:
                        yield (
                            row_number,
                            word,
                            default_weight,
                            f"word exceeds {MAX_TERM_LENGTH} characters",
                        )
                        continue

                    normalized_word = normalize(word)
                    if len(normalized_word) > MAX_TERM_LENGTH:
                        yield (
                            row_number,
                            word,
                            default_weight,
                            f"normalized word exceeds {MAX_TERM_LENGTH} characters after casefold",
                        )
                        continue

                    if len(row) > 2:
                        yield (row_number, word, default_weight, "expected at most two columns")
                        continue

                    if len(row) == 1 or not row[1].strip():
                        yield (row_number, word, default_weight, None)
                        continue

                    try:
                        weight = int(row[1])
                    except ValueError:
                        yield (row_number, word, default_weight, "weight must be an integer")
                        continue

                    if weight < 0:
                        yield (
                            row_number,
                            word,
                            weight,
                            "weight must be greater than or equal to 0",
                        )
                        continue

                    if weight > MAX_WEIGHT:
                        yield (
                            row_number,
                            word,
                            weight,
                            f"weight must be less than or equal to {MAX_WEIGHT}",
                        )
                        continue

                    yield (row_number, word, weight, None)
        except UnicodeDecodeError as exc:
            raise CommandError(f"corpus file is not valid UTF-8: {path} ({exc})") from exc
        except csv.Error as exc:
            raise CommandError(f"corpus file is not valid CSV: {path} ({exc})") from exc
