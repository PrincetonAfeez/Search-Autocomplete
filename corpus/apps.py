""" Corpus app configuration. """

from django.apps import AppConfig

WORD_INVALIDATE_SAVE_UID = "corpus.word.invalidate_engine.save"
WORD_INVALIDATE_DELETE_UID = "corpus.word.invalidate_engine.delete"


def invalidate_engine(**_kwargs) -> None:
    """Signal receiver: clear the lazy engine cache after Word writes."""
    from .loader import clear_engine

    clear_engine()


class CorpusConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "corpus"

    def ready(self) -> None:
        from django.db.models.signals import post_delete, post_save

        from .models import Word

        post_save.connect(invalidate_engine, sender=Word, dispatch_uid=WORD_INVALIDATE_SAVE_UID)
        post_delete.connect(invalidate_engine, sender=Word, dispatch_uid=WORD_INVALIDATE_DELETE_UID)
