""" Corpus models. """

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from autocomplete.constants import MAX_TERM_LENGTH
from autocomplete.normalizer import normalize


class WordQuerySet(models.QuerySet):
    def update(self, **kwargs):
        updated = super().update(**kwargs)
        if updated:
            from .loader import clear_engine

            clear_engine()
        return updated

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False):
        created = super().bulk_create(
            objs,
            batch_size=batch_size,
            ignore_conflicts=ignore_conflicts,
        )
        if created:
            from .loader import clear_engine

            clear_engine()
        return created

    def bulk_update(self, objs, fields, batch_size=None):
        super().bulk_update(objs, fields, batch_size=batch_size)
        if objs:
            from .loader import clear_engine

            clear_engine()


class Word(models.Model):
    text = models.CharField(max_length=255)
    normalized_text = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        editable=False,
        blank=True,
    )
    weight = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = WordQuerySet.as_manager()

    class Meta:
        ordering = ["normalized_text"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(weight__gte=0),
                name="corpus_word_weight_nonnegative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.text} ({self.weight})"

    def clean(self) -> None:
        if not normalize(self.text):
            raise ValidationError({"text": "Word text must not be blank."})
        normalized = normalize(self.text.strip())
        if len(normalized) > MAX_TERM_LENGTH:
            raise ValidationError(
                {"text": f"Normalized text exceeds {MAX_TERM_LENGTH} characters after casefold."}
            )

    def save(self, *args, **kwargs) -> None:
        self.text = self.text.strip()
        self.normalized_text = normalize(self.text)
        self.full_clean()
        super().save(*args, **kwargs)
