# Deployment notes

## Single-process dev (default)

`python manage.py runserver` — one worker, lazy engine singleton, signal/`WordQuerySet` cache invalidation.

## Multi-worker production

Each worker holds its own in-memory trie (ADR 0001). After corpus changes:

1. restart workers, or
2. run `python manage.py rebuild_trie` **in each worker process** (not cross-process).

There is no shared cache or pub/sub invalidation in scope.

## Environment

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Required in production |
| `DJANGO_DEBUG=0` | Disable debug |
| `DJANGO_ALLOWED_HOSTS` | Host allow list |
| `AUTOCOMPLETE_MIN_PREFIX` | Min prefix length (default 2) |
| `AUTOCOMPLETE_LIMIT` | Default top-k (default 10) |

See [ADR 0007](adr/0007-security-posture.md): no rate limiting, TLS, or CSP in this repo — add at the reverse proxy for public deployment.
