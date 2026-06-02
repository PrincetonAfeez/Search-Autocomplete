""" Web views. """

from django.shortcuts import render
from django.views.decorators.http import require_GET

from autocomplete.constants import MAX_TERM_LENGTH
from corpus.loader import get_engine


@require_GET
def search(request):
    return render(request, "web/search.html")


@require_GET
def suggest(request):
    query = request.GET.get("q", "")[:MAX_TERM_LENGTH]
    engine = get_engine()
    suggestions = engine.suggest(query)

    rows = [
        {
            "word": suggestion.word,
            "prefix": suggestion.word[: suggestion.matched_display_length],
            "suffix": suggestion.word[suggestion.matched_display_length :],
            "weight": suggestion.weight,
        }
        for suggestion in suggestions
    ]

    response = render(
        request,
        "web/partials/suggestions.html",
        {
            "normalized_query": engine.normalize_query(query),
            "suggestions": rows,
            "is_too_short": engine.is_too_short(query),
        },
    )
    response["Cache-Control"] = "no-store"
    return response
