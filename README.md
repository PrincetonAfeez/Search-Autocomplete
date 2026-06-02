# Search Autocomplete

[![CI](https://github.com/your-username/search-autocomplete/actions/workflows/test.yml/badge.svg)](https://github.com/your-username/search-autocomplete/actions/workflows/test.yml)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![Coverage ≥85%](https://img.shields.io/badge/coverage-%E2%89%A585%25-green)
![License MIT](https://img.shields.io/badge/license-MIT-blue)

A Django + HTMX autocomplete app backed by a **hand-built Python trie**.

> **Security note:** intended for localhost / academic use. See [ADR 0007](docs/adr/0007-security-posture.md) before exposing publicly.

## Problem statement

**Input:** a prefix string (≤255 chars) typed by a user.  
**Output:** up to *k* corpus words that start with that prefix (case-insensitive), ranked by static weight then alphabetically.  
**Constraints:** exact prefix only; single-process in-memory index; DB is source of truth.  
**Non-goals:** fuzzy matching, personalization, distributed cache invalidation.

## Quick start

```powershell
pip install -e ".[dev]"
playwright install chromium
python manage.py migrate
python manage.py seed_corpus data/words.csv
python manage.py runserver
```

Open http://127.0.0.1:8000/search/ and type `py`, `da`, or `tr`.

Reproducible install (CI canonical):

```powershell
pip install -r requirements.lock
pip install -e . --no-deps
pip install -e ".[test]"
```

Windows task runner: `.\tasks.ps1 install-dev` · Unix: `make install-dev`

## Demo

See [`docs/demo.md`](docs/demo.md) for capture instructions. Architecture diagrams live in [`docs/architecture.md`](docs/architecture.md).

## Endpoints

| Path | Method | Description |
| --- | --- | --- |
| `/` | GET | Redirects to `/search/`. |
| `/search/` | GET | Search page. |
| `/suggest/?q=<prefix>` | GET | HTMX suggestions partial (`Cache-Control: no-store`). |
| `/admin/` | GET | Word CRUD; batch actions invalidate engine cache. |

## Architecture

```text
web -> corpus.loader -> autocomplete
corpus -> autocomplete
cli -> corpus.loader -> autocomplete
```

Details: [`docs/architecture.md`](docs/architecture.md) · Complexity: [`docs/complexity.md`](docs/complexity.md) · ADRs: [`docs/adr/`](docs/adr/)

### Why a trie?

| Approach | Prefix search | Ranking | Fit here |
| --- | --- | --- | --- |
| **Trie** | O(p) walk + O(m) collect | Static top-k | Teaching-friendly, explicit index |
| Hash map | O(n) scan | Any | No natural prefix grouping |
| SQL `LIKE` | Index-dependent | SQL sort | Hides index; project goal is hand-built structure |

## Commands

```powershell
python manage.py seed_corpus data/words.csv   # --clear --dry-run --delimiter ";"
python manage.py rebuild_trie
python cli.py py                              # or: search-autocomplete py
python scripts/benchmark_suggest.py           # latency benchmark
```

## Quality gates

```powershell
make test          # or .\tasks.ps1 test
make lint          # ruff check + format
make typecheck     # mypy autocomplete/
make coverage      # pytest --cov (≥85%)
make audit         # pip-audit
```

Test plan: [`docs/test-plan.md`](docs/test-plan.md) · Evaluation write-up: [`docs/evaluation.md`](docs/evaluation.md)

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | dev key | Session/CSRF secret |
| `DJANGO_DEBUG` | `1` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | localhost | Host allow list |
| `AUTOCOMPLETE_MIN_PREFIX` | `2` | Min normalized prefix length |
| `AUTOCOMPLETE_LIMIT` | `10` | Default top-k |

Bulk ORM writes (`update`, `bulk_update`, `bulk_create`) invalidate the engine via `WordQuerySet`.

## Limits

| Limit | Value |
| --- | --- |
| Max query / word length | 255 chars |
| Min prefix | 2 (configurable) |
| Default top-K | 10 (configurable) |
| Top-K time | O(m) nodes under prefix; O(k) memory |

Comfortable locally through **~50k words**; short prefixes on dense corpora visit more nodes. See [`docs/complexity.md`](docs/complexity.md).

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Empty suggestions after seed | Run `migrate`, then `seed_corpus data/words.csv` from repo root |
| Stale suggestions after shell edit | `from corpus.loader import clear_engine; clear_engine()` or use `Word.objects.update()` |
| `ImproperlyConfigured` on startup | Check `AUTOCOMPLETE_*` env vars are valid integers |
| Playwright e2e fails | Run `playwright install chromium` |
| Multi-worker stale index | `rebuild_trie` per worker or restart (see [`docs/deployment.md`](docs/deployment.md)) |

## Scope

**Implemented:** exact prefix, casefold, display-aligned highlighting, static ranking, trie delete/prune, signal + queryset cache invalidation, HTMX + ARIA combobox (e2e tested).

**Not implemented:** fuzzy search, adaptive ranking, trie snapshots, NFC normalization, cross-process invalidation.

## License

MIT — see [LICENSE](LICENSE). Changelog: [CHANGELOG.md](CHANGELOG.md).
