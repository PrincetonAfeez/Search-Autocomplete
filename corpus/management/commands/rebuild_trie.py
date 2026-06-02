""" Rebuild trie command. """

from django.core.management.base import BaseCommand

from corpus.loader import rebuild_engine


class Command(BaseCommand):
    help = "Validate that the in-process autocomplete engine can be rebuilt from the DB."

    def handle(self, *args, **options) -> None:
        engine = rebuild_engine()
        size = len(engine.trie)
        message = f"rebuilt autocomplete engine with {size} active words"

        if size == 0:
            self.stdout.write(self.style.WARNING(message + " (corpus is empty)"))
        else:
            self.stdout.write(self.style.SUCCESS(message))
