# Architecture Decision Record
## App — Search Autocomplete
**Autocomplete Systems Group | Document 1 of 5**
**Status: Accepted**

---

## Context

The Autocomplete Systems group requires a portfolio-ready Django + HTMX autocomplete application backed by a hand-built Python trie. The system accepts a prefix string typed by a user and returns up to `k` corpus words that begin with that prefix. Matching is exact-prefix and case-insensitive. Ranking is static: higher `weight` wins, with normalized alphabetical ordering as the tie-breaker.

The application has two roles:

1. **Algorithmic demonstration:** prove the trie data structure, normalization, top-k selection, deletion/pruning, and complexity trade-offs are understood and implemented directly.
2. **Web product demonstration:** expose the autocomplete behavior through an HTMX UI with accessible combobox behavior and a Django-backed corpus.

The database is the source of truth. The trie is a process-local in-memory read model rebuilt from active database rows. The app is intentionally scoped for localhost / academic portfolio use, not as a distributed production search service.

---

## Decisions

### Decision 1 — Use a hand-built Python trie for exact prefix search

**Chosen:** Store normalized words in a trie implemented in `autocomplete.trie`.

**Rejected:** SQL `LIKE`, database full-text search, external search engines, Redis autocomplete, or fuzzy libraries.

**Reason:** The goal is to demonstrate the data structure directly. SQL would hide the indexing behavior. External search engines would exceed the learning scope. A trie makes prefix traversal explicit and keeps the algorithm teachable.

---

### Decision 2 — Treat the database as source of truth and trie as cache

**Chosen:** Store corpus words in Django `Word` rows and rebuild the trie from active rows.

**Rejected:** Making the trie the primary persistent store.

**Reason:** Django provides validation, migrations, admin CRUD, and a stable authoritative corpus. The trie is optimized for read-time suggestions and can be rebuilt whenever needed.

---

### Decision 3 — Use process-local lazy engine construction

**Chosen:** `corpus.loader.get_engine()` lazily builds a singleton `AutocompleteEngine` guarded by a `threading.Lock`.

**Rejected:** Rebuilding the trie on every request.

**Reason:** Rebuilding on every keystroke would waste CPU and database I/O. A lazy in-process cache keeps request handling simple and fast for the documented local/academic scope.

---

### Decision 4 — Invalidate cache on Word writes

**Chosen:** Invalidate the cached engine on model saves/deletes, queryset bulk writes, and admin deletion.

**Rejected:** Letting the trie remain stale until manual restart only.

**Reason:** The DB is source of truth, so updates must eventually flow into the in-memory read model. The app invalidates on writes and rebuilds lazily on the next request.

---

### Decision 5 — Accept single-process cache limits

**Chosen:** No cross-process invalidation.

**Rejected:** Redis pub/sub, database notification channels, or shared trie snapshots.

**Reason:** The README explicitly scopes the app to single-process in-memory indexing. Multi-worker deployment would need explicit per-worker rebuild/restart handling.

---

### Decision 6 — Normalize with `strip().casefold()`

**Chosen:** Normalize both corpus words and query prefixes using `strip().casefold()`.

**Rejected:** ASCII-only lowercasing or full Unicode NFC normalization.

**Reason:** `casefold()` is stronger than `.lower()` and handles more Unicode case behavior. NFC normalization is deferred because it introduces additional Unicode rules beyond the core prefix-search scope.

---

### Decision 7 — Preserve display text separately from normalized text

**Chosen:** Trie nodes store both display `word` and `normalized_word`.

**Rejected:** Displaying normalized strings directly.

**Reason:** Users should see the original corpus word, not a normalized key. Separate fields also allow display-aligned highlighting.

---

### Decision 8 — Compute display-aligned highlight length

**Chosen:** `display_match_length()` maps normalized prefix length back to display characters.

**Rejected:** Slicing display text by normalized prefix length.

**Reason:** `casefold()` can expand a character, such as `ß -> ss`. Direct slicing can split or over-highlight display characters. The mapping function prevents that.

---

### Decision 9 — Rank by weight, then normalized word

**Chosen:** Suggestions are ranked by higher static weight first, then normalized alphabetical order.

**Rejected:** Recency, personalized ranking, fuzzy scoring, or adaptive click ranking.

**Reason:** Static ranking is deterministic and testable. It keeps the project focused on trie indexing rather than personalization systems.

---

### Decision 10 — Use bounded heap for top-k

**Chosen:** `collect_top_k()` traverses the prefix subtree and keeps only the best `k` candidates in a heap.

**Rejected:** Collecting all suggestions, sorting the full list, then slicing.

**Reason:** The trie may contain many descendants under a short prefix. Keeping only `k` candidates bounds result memory to `O(k)` while still visiting all matching nodes.

---

### Decision 11 — Use HTMX partial rendering for suggestions

**Chosen:** The page uses an input with `hx-get` to `/suggest/` and swaps a Django-rendered suggestions partial.

**Rejected:** Building a JSON API plus client-side rendering.

**Reason:** HTMX keeps the app server-rendered and focused. It demonstrates progressive interaction without adding a frontend framework.

---

### Decision 12 — Add ARIA combobox behavior in small JavaScript

**Chosen:** Use a lightweight `autocomplete.js` layer for keyboard navigation, active option state, closing behavior, `aria-expanded`, `aria-controls`, and `aria-activedescendant`.

**Rejected:** Leaving the widget as a plain input plus list only.

**Reason:** Autocomplete is an interactive control. The UI should be usable with keyboard and assistive technology patterns, even in a small academic app.

---

## Consequences

**Positive:**
- Core algorithm is explicit and portfolio-visible.
- DB remains authoritative and inspectable through Django admin.
- Lazy cache avoids rebuilding per request.
- Cache invalidation is handled for common ORM/admin mutation paths.
- Exact-prefix behavior is deterministic.
- Top-k selection uses bounded memory.
- HTMX keeps the web layer simple.
- CLI and web share the same engine.
- Unicode casefold behavior is handled more carefully than ASCII lowercasing.
- E2E browser testing validates the interaction layer.

**Negative / Trade-offs:**
- No fuzzy matching.
- No personalization.
- No cross-process cache invalidation.
- Dense short prefixes still require scanning many trie descendants.
- Ranking is static and must be maintained in the corpus.
- No persisted trie snapshot.
- SQLite/default Django settings are suitable for local use, not production as-is.
- HTMX partials are HTML-only; no JSON suggestions API is provided.
- Unicode normalization is casefold-only; NFC/NFKC equivalence is out of scope.

---

## Alternatives Not Explored

- SQL indexed `LIKE` query.
- PostgreSQL trigram search.
- Redis autocomplete.
- Elasticsearch/OpenSearch.
- DAWG/radix tree/compressed trie.
- Fuzzy search.
- Adaptive ranking.
- Cross-worker invalidation.
- Trie serialization/snapshots.
- JSON API and client-rendered frontend.
- User-specific personalization.

---

*Constitution reference: Article 1 (Python fundamentals and architectural thinking), Article 3.3 (scope discipline), Article 4 (quality proportional to scope), Article 5 (trade-off documentation), Article 6 (verification), and Article 7 (progressive complexity).*

---


# Technical Design Document
## App — Search Autocomplete
**Autocomplete Systems Group | Document 2 of 5**

---

## Overview

Search Autocomplete is a Django + HTMX application with a hand-built trie-based autocomplete engine. It includes:

- `autocomplete`: pure Python trie, normalizer, suggestion model, engine wrapper
- `corpus`: Django model, admin, loader, seed/rebuild commands
- `web`: search page, suggestions endpoint, templates, static JS/CSS
- `config`: Django settings/URLs
- `cli.py`: command-line autocomplete REPL and one-shot prefix query

**Package:** `search-autocomplete`  
**Python:** `>=3.11`  
**Framework:** Django 5.2  
**Core algorithm:** exact prefix trie  
**UI:** Django templates + HTMX + ARIA JavaScript  
**Default DB:** SQLite  
**Testing:** pytest, pytest-django, Playwright, coverage threshold 85%

---

## System Context

```text
Browser
  │
  │ GET /search/
  ▼
Django search page
  │
  │ keyup changed delay:250ms
  │ GET /suggest/?q=<prefix>
  ▼
web.views.suggest
  │
  ▼
corpus.loader.get_engine()
  │
  ├── lazy build if cache empty
  │   └── Word.objects.filter(is_active=True)
  │       └── Trie.insert(text, weight)
  │
  ▼
AutocompleteEngine.suggest()
  │
  ▼
Trie.collect_top_k()
  │
  ▼
suggestions.html partial
  │
  ▼
HTMX swaps list into page
```

---

## Module-Level Structure

```text
Search-Autocomplete/
  autocomplete/
    constants.py
    engine.py
    normalizer.py
    suggestion.py
    trie.py
  corpus/
    admin.py
    apps.py
    loader.py
    models.py
    management/commands/seed_corpus.py
    management/commands/rebuild_trie.py
  web/
    views.py
    urls.py
    templates/web/search.html
    templates/web/partials/suggestions.html
    static/web/autocomplete.js
  config/
    settings.py
    urls.py
  cli.py
  manage.py
  pyproject.toml
  requirements.lock
  requirements-dev.lock
  Makefile
  tasks.ps1
```

---

## Module Dependency Graph

```text
web.views
  ├── autocomplete.constants.MAX_TERM_LENGTH
  └── corpus.loader.get_engine

corpus.loader
  ├── autocomplete.AutocompleteEngine
  ├── autocomplete.Trie
  ├── django.conf.settings
  └── corpus.models.Word

corpus.models
  ├── autocomplete.constants
  ├── autocomplete.normalizer.normalize
  └── corpus.loader.clear_engine

corpus.apps
  ├── django post_save / post_delete
  └── corpus.loader.clear_engine

seed_corpus
  ├── csv
  ├── transaction.atomic
  ├── autocomplete constants / normalize
  ├── corpus.models.Word
  └── corpus.loader.clear_engine

cli.py
  ├── django.setup
  ├── corpus.loader.get_engine
  └── corpus.loader.rebuild_engine
```

---

## Core Data Structures

### `TrieNode`

```python
@dataclass(slots=True)
class TrieNode:
    children: dict[str, TrieNode]
    is_word: bool
    word: str | None
    normalized_word: str | None
    weight: int
```

Each node represents one normalized prefix path. Terminal nodes store the display word, normalized word, and weight.

---

### `Trie`

Primary methods:
- `insert(word, weight=1)`
- `contains(word)`
- `starts_with(prefix)`
- `collect(prefix)`
- `collect_top_k(prefix, k)`
- `delete(word)`

State:
- `root`
- `_size`

Validation:
- word cannot normalize empty
- display word length ≤ 255
- normalized word length ≤ 255
- weight must be between `0` and `2_147_483_647`

---

### `Suggestion`

```python
@dataclass(frozen=True, slots=True)
class Suggestion:
    word: str
    normalized_word: str
    weight: int
    matched_length: int
    matched_display_length: int
```

Represents one display-ready match.

---

### `AutocompleteEngine`

Wrapper over `Trie` that enforces:
- minimum normalized prefix length
- default result limit
- query truncation to max term length
- empty result for blank or too-short prefixes

Primary methods:
- `contains(word)`
- `normalize_query(prefix)`
- `is_too_short(prefix)`
- `suggest(prefix, k=None)`
- `rebuild(words)`

---

### `Word`

Django model fields:
- `text`
- `normalized_text`
- `weight`
- `is_active`
- `created_at`
- `updated_at`

Important behavior:
- `normalized_text` is unique and indexed
- `save()` strips text, computes normalized text, validates, then saves
- model constraints enforce weight bounds
- queryset bulk operations clear the cached engine

---

## Algorithms

### Insert

```text
insert(word, weight)
  display_word = word.strip()
  normalized_word = normalize(word)

  validate display/normalized text and weight

  node = root
  for char in normalized_word:
      node = node.children.setdefault(char, TrieNode())

  if node was not terminal:
      size += 1

  mark node terminal
  store display word, normalized word, weight
```

Complexity:
```text
O(p)
```
where `p` is normalized word length.

---

### Exact Prefix Suggest

```text
suggest(prefix, k)
  truncate prefix to max length
  normalize
  if blank or shorter than min prefix:
      return []

  walk trie to prefix node
  if missing:
      return []

  traverse subtree
  for each terminal word:
      compute suggestion
      rank = (-weight, normalized_word)
      keep only best k in bounded heap

  return heap sorted by rank
```

Complexity:
```text
O(p + m log k)
```
where `p` is prefix length, `m` is terminal words below the prefix subtree, and `k` is requested result count.

Memory:
```text
O(k)
```
for the candidate heap, excluding trie storage.

---

### Delete and Prune

```text
delete(word)
  normalize
  walk path, recording parent/char pairs
  if terminal missing:
      return False

  clear terminal fields
  size -= 1

  walk path backward
      delete child if it has no children and is not terminal
      stop at first live node
```

---

### Display Highlight Mapping

`display_match_length()` walks display characters and counts their casefold length so highlighting never splits an expanded character.

---

## Web Request Flow

### `/search/`

Returns the full search page with:
- search input
- HTMX attributes
- ARIA combobox role
- suggestions target
- static CSS/JS

### `/suggest/?q=<prefix>`

Steps:
1. Read `q`.
2. Truncate to 255 characters.
3. Get cached engine.
4. Ask engine for suggestions.
5. Convert each `Suggestion` into `{word, prefix, suffix, weight}`.
6. Render `web/partials/suggestions.html`.
7. Set `Cache-Control: no-store`.

---

## Cache Invalidation

Engine cache can be cleared by:
- `post_save` on `Word`
- `post_delete` on `Word`
- `WordQuerySet.update()`
- `WordQuerySet.bulk_create()`
- `WordQuerySet.bulk_update()`
- admin `delete_queryset`
- seed command after import
- direct call to `clear_engine()`

Seed command detaches save/delete signals during bulk import to avoid repeated invalidations, then clears the engine once at the end.

---

## Error Handling Strategy

### Engine/trie errors

Raised as Python `ValueError` / `TypeError` for invalid constructor arguments, invalid terms, invalid weights, or non-string normalization input.

### Django configuration errors

Invalid `AUTOCOMPLETE_*` values raise `ImproperlyConfigured` at settings load.

### Management command errors

`seed_corpus` raises `CommandError` for:
- missing file
- non-file path
- invalid default weight
- non-UTF-8 input
- malformed CSV

Invalid rows are reported per line and counted in the import summary.

### CLI errors

`cli.py` returns:
- `0` for successful query/REPL/help/version and successful no-match/too-short results
- `2` for usage/configuration errors such as `--limit < 1`

---

## External Dependencies

### Runtime

- Django `>=5.2,<6`

### Development / Test

- pytest
- pytest-cov
- pytest-django
- hypothesis
- playwright
- pytest-playwright
- ruff
- mypy
- pip-audit
- pip-tools

---

## Concurrency Model

- Web requests read from a process-local engine.
- Engine construction is guarded by a `threading.Lock`.
- The trie itself is read after construction.
- Cache invalidation swaps `_engine` to `None`.
- Multi-process cache invalidation is not implemented.

---

## Known Limits

- Maximum query/word length: 255 chars.
- Maximum weight: `2_147_483_647`.
- Default min prefix: 2.
- Default top-k: 10.
- Dense short prefixes visit many subtree nodes.
- Comfortable local corpus documented around 50k words.
- No fuzzy matching.
- No adaptive ranking.
- No cross-process invalidation.
- No persisted trie snapshot.
- No NFC normalization.

---

*Constitution reference: Article 4 (engineering quality), Article 6 (behavior verification), Article 7 (progressive complexity), and Article 8 (valid learner work).*

---


# Interface Design Specification
## App — Search Autocomplete
**Autocomplete Systems Group | Document 3 of 5**

---

## Public Web Interface

### `GET /`

Redirects to `/search/`.

---

### `GET /search/`

Returns the full search page.

Important UI contract:
- input name: `q`
- max length: `255`
- role: `combobox`
- autocomplete mode: `list`
- HTMX target: `#suggestions`
- trigger: `keyup changed delay:250ms, search`
- suggestions are inserted into `#suggestions`

---

### `GET /suggest/?q=<prefix>`

Returns an HTML partial.

Query parameter:

| Name | Required | Description |
|---|---:|---|
| `q` | No | User prefix; truncated to 255 characters |

Response behavior:

| Condition | Response |
|---|---|
| normalized query is blank | empty partial |
| normalized query is shorter than min prefix | `Keep typing` |
| no suggestions | `No matches found` |
| suggestions exist | `<ul role="listbox">` containing `<li role="option">` rows |

Header:

```text
Cache-Control: no-store
```

---

## Suggestions Partial Contract

Each suggestion row contains:
- full word in `data-word`
- highlighted prefix in `<strong>`
- suffix as normal text
- weight displayed in a secondary span
- `role="option"`
- `aria-selected="false"` initially
- stable id based on loop index

---

## JavaScript Interaction Contract

The autocomplete controller:
- tracks options in `#suggestions`
- sets `aria-expanded`
- sets `aria-controls`
- sets `aria-activedescendant`
- sets `aria-busy` during HTMX request
- supports ArrowDown/ArrowUp cycling
- supports Enter selection
- supports Tab selection when active
- supports Escape close
- closes on outside pointerdown
- supports pointer hover activation
- suppresses stale HTMX swaps after local close

---

## Public Python Library Interface

### Import

```python
from autocomplete import AutocompleteEngine, Trie
```

Additional internal modules:

```python
from autocomplete.normalizer import normalize, display_match_length
from autocomplete.suggestion import Suggestion
```

---

### `Trie`

```python
trie = Trie()
trie.insert("python", weight=100)
trie.contains("PYTHON")
trie.starts_with("py")
trie.collect_top_k("py", 10)
trie.delete("python")
```

#### `insert(word: str, weight: int = 1) -> None`

Validation:
- word must normalize to non-empty
- display word length ≤ 255
- normalized word length ≤ 255
- weight ≥ 0
- weight ≤ `2_147_483_647`

Updates existing normalized word if inserted again.

---

#### `collect_top_k(prefix: str, k: int) -> list[Suggestion]`

Returns ranked suggestions.

Ranking:

```text
1. higher weight first
2. normalized alphabetical order
```

Special cases:
- `k <= 0` returns `[]`
- blank normalized prefix returns `[]`
- unmatched prefix returns `[]`

---

#### `delete(word: str) -> bool`

Returns:
- `True` if a terminal word was removed
- `False` if word was blank, missing, or only a prefix

Side effect:
- prunes dead nodes on the deleted path

---

### `AutocompleteEngine`

```python
engine = AutocompleteEngine(min_prefix_length=2, default_limit=10)
engine.rebuild([("python", 100), ("pytest", 80)])
engine.suggest("py")
```

Constructor rules:
- `min_prefix_length >= 0`
- `default_limit >= 1`

Methods:
- `contains(word)`
- `normalize_query(prefix)`
- `is_too_short(prefix)`
- `suggest(prefix, k=None)`
- `rebuild(words)`

---

## Public Django Model Interface

### `Word`

Fields:

| Field | Type | Contract |
|---|---|---|
| `text` | CharField(255) | Display word |
| `normalized_text` | CharField(255) | Unique indexed normalized key |
| `weight` | PositiveIntegerField | 0 through 2,147,483,647 |
| `is_active` | BooleanField | Only active rows load into trie |
| `created_at` | DateTimeField | auto set |
| `updated_at` | DateTimeField | auto updated |

Save behavior:
- strips `text`
- computes `normalized_text`
- calls `full_clean()`
- saves row

---

## Management Commands

### `seed_corpus`

```powershell
python manage.py seed_corpus data/words.csv
python manage.py seed_corpus data/words.csv --clear
python manage.py seed_corpus data/words.csv --dry-run
python manage.py seed_corpus data/words.csv --delimiter ";"
python manage.py seed_corpus data/words.csv --default-weight 5
```

Input formats:

```text
word
word,weight
```

Rules:
- UTF-8 input
- blank rows skipped
- blank words invalid
- words ≤ 255 chars
- normalized words ≤ 255 chars
- weight integer from 0 to `2_147_483_647`
- duplicate normalized keys update existing rows
- dry run reports would-create/would-update counts without writing
- clear deletes existing rows before import

Success output:

```text
seed complete: created=<n>, updated=<n>, invalid=<n>
```

Dry run output:

```text
dry run complete: would_create=<n>, would_update=<n>, invalid=<n>
```

---

### `rebuild_trie`

```powershell
python manage.py rebuild_trie
```

Behavior:
- rebuilds process-local engine from active DB rows
- prints active word count
- warns when corpus is empty

---

## CLI Interface

### One-shot query

```powershell
python cli.py py
search-autocomplete py
```

### REPL

```powershell
python cli.py
```

### Options

| Option | Description |
|---|---|
| `--version` | Print package version |
| `--limit N` | Maximum suggestions for one query/REPL |
| `--rebuild` | Rebuild engine from DB before use |
| `prefix` | Optional one-shot prefix |

Validation:
- `--limit < 1` prints an error and returns 2

Output cases:

```text
Keep typing
No matches
1. python               100
```

Exit codes:

| Code | Meaning |
|---:|---|
| `0` | Success, no-match, too-short, help/version, REPL |
| `2` | Usage/configuration error |

---

## Configuration Interface

Environment variables:

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | development key | Django secret |
| `DJANGO_DEBUG` | `1` | Enables debug when `1` |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Host allow list |
| `DJANGO_LOG_LEVEL` | `INFO` | Django logger level |
| `AUTOCOMPLETE_MIN_PREFIX` | `2` | Minimum normalized prefix length |
| `AUTOCOMPLETE_LIMIT` | `10` | Default suggestion limit |

Validation:
- `AUTOCOMPLETE_MIN_PREFIX` must be integer ≥ 0
- `AUTOCOMPLETE_LIMIT` must be integer ≥ 1

Invalid values raise `ImproperlyConfigured`.

---

## Side Effects

| Operation | Side Effect |
|---|---|
| `/suggest/` | Reads cached trie / may lazy build from DB |
| `seed_corpus` | Writes/updates/deletes `Word` rows unless dry-run |
| `rebuild_trie` | Replaces process-local in-memory engine |
| `Word.save()` | Computes normalized text and clears cache via signal |
| `WordQuerySet.update()` | Clears cache |
| `WordQuerySet.bulk_create()` | Clears cache |
| `WordQuerySet.bulk_update()` | Clears cache |
| Admin delete | Clears cache |
| CLI `--rebuild` | Rebuilds process-local engine |

---

*Constitution reference: Article 4 (input/output boundaries), Article 6 (verification), and Article 8 (understandable and verifiable work).*

---


# Runbook
## App — Search Autocomplete
**Autocomplete Systems Group | Document 4 of 5**

---

## Requirements

### Runtime

- Python 3.11 or newer
- Django 5.2
- SQLite for local development

### Development

- pytest
- pytest-django
- pytest-cov
- hypothesis
- Playwright + Chromium
- ruff
- mypy
- pip-audit
- pip-tools

---

## Installation

### Development install

```powershell
pip install -e ".[dev]"
playwright install chromium
```

### Reproducible CI-style install

```powershell
pip install -r requirements-dev.lock
pip install -e . --no-deps
playwright install chromium
```

### Runtime-only install

```powershell
pip install -r requirements.lock
pip install -e . --no-deps
```

---

## Initial Setup

```powershell
python manage.py migrate
python manage.py seed_corpus data/words.csv
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/search/
```

Try prefixes:

```text
py
da
tr
```

---

## Standard Operating Procedures

### Seed corpus

```powershell
python manage.py seed_corpus data/words.csv
```

Clear first:

```powershell
python manage.py seed_corpus data/words.csv --clear
```

Validate without writing:

```powershell
python manage.py seed_corpus data/words.csv --dry-run
```

Use alternate delimiter:

```powershell
python manage.py seed_corpus data/words.csv --delimiter ";"
```

---

### Rebuild trie

```powershell
python manage.py rebuild_trie
```

Expected:

```text
rebuilt autocomplete engine with <n> active words
```

---

### Query from CLI

```powershell
python cli.py py
search-autocomplete py
```

With limit:

```powershell
search-autocomplete --limit 5 py
```

With rebuild:

```powershell
search-autocomplete --rebuild py
```

REPL:

```powershell
search-autocomplete
```

---

## Quality Checks

### Tests

```powershell
python -m pytest
```

### Coverage

```powershell
python -m pytest --cov --cov-report=term-missing
```

Coverage gate:

```text
85%
```

### Lint

```powershell
ruff check .
ruff format --check .
```

### Typecheck

```powershell
mypy autocomplete
```

### Security audit

```powershell
pip-audit -r requirements-dev.lock
```

### E2E

```powershell
python -m pytest -m e2e
```

---

## Health Checks

### Django startup

```powershell
python manage.py check
```

Expected:

```text
System check identified no issues
```

---

### Engine rebuild

```powershell
python manage.py rebuild_trie
```

Expected:

```text
rebuilt autocomplete engine with <n> active words
```

---

### HTTP suggestions

After running server:

```text
GET /suggest/?q=py
```

Expected:
- HTTP 200
- `Cache-Control: no-store`
- HTML partial with suggestions or empty-state message

---

### CLI query

```powershell
python cli.py py
```

Expected:
- ranked suggestions, `Keep typing`, or `No matches`
- exit code 0

---

### Bad CLI limit

```powershell
python cli.py --limit 0 py
```

Expected:

```text
error: --limit must be greater than or equal to 1
```

Exit:

```text
2
```

---

## Expected Outputs

### Too-short prefix

```text
Keep typing
```

### No matches

```text
No matches
```

### Suggestions

```text
1. python               100
2. pytest               80
```

### Seed success

```text
seed complete: created=10, updated=2, invalid=0
```

### Dry run

```text
dry run complete: would_create=10, would_update=2, invalid=0
```

---

## Known Failure Modes

### Empty suggestions after seed

**Cause:** Database not migrated, seed command not run, or running from wrong repo/root.

**Fix:**

```powershell
python manage.py migrate
python manage.py seed_corpus data/words.csv
python manage.py rebuild_trie
```

---

### Stale suggestions after manual shell edit

**Cause:** Direct changes may not pass through normal invalidation path.

**Fix:**

```python
from corpus.loader import clear_engine
clear_engine()
```

or use ORM operations that trigger invalidation.

---

### Invalid autocomplete settings

**Symptom:**

```text
ImproperlyConfigured
```

**Cause:** `AUTOCOMPLETE_MIN_PREFIX` or `AUTOCOMPLETE_LIMIT` is not an integer or below minimum.

**Fix:**

```powershell
$env:AUTOCOMPLETE_MIN_PREFIX = "2"
$env:AUTOCOMPLETE_LIMIT = "10"
```

---

### Playwright e2e fails

**Cause:** Chromium not installed.

**Fix:**

```powershell
playwright install chromium
```

---

### Multi-worker stale index

**Cause:** Engine cache is process-local.

**Fix:**
- run `rebuild_trie` per worker
- restart workers after corpus changes
- add cross-process invalidation in a future version

---

### Dense short prefixes are slow

**Cause:** Top-k still must visit all terminal words under the prefix subtree.

**Fix:**
- raise `AUTOCOMPLETE_MIN_PREFIX`
- reduce corpus density
- add cached top-k per node in a future version

---

## Troubleshooting Decision Tree

```text
Suggestions missing
  ├── Is DB migrated?
  │     └── run manage.py migrate
  ├── Is corpus seeded?
  │     └── run seed_corpus
  ├── Are words active?
  │     └── check admin is_active
  ├── Is prefix too short?
  │     └── type at least AUTOCOMPLETE_MIN_PREFIX chars
  ├── Is cache stale?
  │     └── rebuild_trie or clear_engine()
  └── Are env settings invalid?
        └── verify AUTOCOMPLETE_* values

UI broken
  ├── Are static files loading?
  │     └── check htmx/autocomplete.js requests
  ├── Are HTMX requests firing?
  │     └── check /suggest/?q=... network request
  └── Is ARIA list updating?
        └── inspect #suggestions partial

CLI broken
  ├── Was package installed?
  │     └── pip install -e .
  ├── Is DJANGO_SETTINGS_MODULE available?
  │     └── cli sets config.settings automatically
  └── Is --limit valid?
        └── must be >= 1
```

---

## Maintenance Notes

- Keep trie behavior independent from Django.
- Keep DB as source of truth.
- Add tests before changing ranking.
- Add tests before changing Unicode normalization.
- Preserve cache invalidation on all write paths.
- Keep `/suggest/` non-cacheable.
- Keep HTMX response HTML partial-only unless adding a separate JSON API.
- Keep ARIA combobox behavior tested through e2e.
- Do not expose publicly without revisiting the security posture ADR.
- Document any move to multi-process invalidation.

---

*Constitution reference: Article 6 (behavior verification), Article 5 (constraints and trade-offs), and Article 8 (verifiable learner work).*

---


# Lessons Learned
## App — Search Autocomplete
**Autocomplete Systems Group | Document 5 of 5**

---

## Why This Design Was Chosen

This design was chosen because autocomplete is a strong project for combining a visible data structure with a real user interface. A trie makes prefix lookup concrete. Django makes the corpus manageable. HTMX keeps the web interaction small enough to understand without hiding behavior behind a full JavaScript framework.

The key architectural split is that `autocomplete` is pure Python, while `corpus` and `web` adapt it to Django. That split keeps the algorithm testable outside the web stack and prevents the UI from becoming the source of search behavior.

The database/trie relationship is also important. The database owns the truth. The trie owns fast read behavior. That is a realistic pattern: persistent source of truth plus an optimized read model.

---

## What Was Intentionally Omitted

**Fuzzy matching:** Deferred because it would change the algorithm from exact-prefix trie traversal to edit-distance or phonetic ranking.

**Personalized ranking:** Deferred because it would require user/session signals and ranking history.

**Adaptive ranking:** Deferred because static weight is enough for deterministic behavior.

**Cross-process invalidation:** Deferred because the app is scoped to local/single-process use.

**Trie snapshots:** Deferred because the trie rebuild is simple and adequate for the documented scale.

**NFC normalization:** Deferred because Unicode normalization requires a separate, explicit policy.

**JSON API:** Deferred because HTMX partial rendering satisfies the UI requirement.

---

## Biggest Weakness

The biggest weakness is cache scope. The engine is process-local, so multiple workers can become inconsistent unless they are manually rebuilt or restarted. This is acceptable for localhost and academic use, but it is the first architecture issue that would need attention before production deployment.

The second weakness is dense-prefix traversal. The bounded heap keeps memory to `O(k)`, but it still visits the subtree under the prefix. For very common prefixes, this can be a lot of nodes.

The third weakness is static ranking. It is deterministic, but it cannot learn from user behavior or context.

---

## Scaling Considerations

**If corpus size grows:**
- add cached top-k suggestions on trie nodes
- add compressed trie/radix tree representation
- measure memory usage per corpus size
- consider persisted trie snapshots

**If deployment becomes multi-worker:**
- add cross-process invalidation
- add Redis or database notification channel
- rebuild engine on worker boot
- document restart semantics

**If ranking grows:**
- introduce a ranking interface
- separate static weight from dynamic score
- preserve deterministic fallback sorting
- add tests for tie-breaking and stable output

**If API consumers are added:**
- create `/api/suggest/`
- return JSON with word, weight, prefix/suffix spans
- keep existing HTMX endpoint stable

---

## What the Next Refactor Would Be

1. **Top-k cache per trie node** — store best suggestions at insertion time to make query time closer to `O(p + k)`.

2. **Explicit engine versioning** — track a corpus revision and expose it for debugging stale caches.

3. **JSON suggestions endpoint** — add a separate API without disrupting HTMX partials.

4. **Unicode normalization policy** — decide whether NFC or NFKC should be applied and migrate corpus keys accordingly.

5. **Cross-process invalidation** — add a production-grade invalidation story before public deployment.

---

## What This Project Taught

- **A data structure becomes different when it serves a web UI.** Trie lookup is only one part of autocomplete; request timing, partial rendering, ARIA behavior, and stale-cache rules matter too.

- **Source of truth and read model should be distinct.** Django owns persistence. The trie owns fast lookup.

- **Invalidation is architecture.** Cache invalidation must be handled for saves, deletes, bulk writes, admin actions, and seed commands.

- **Unicode case handling affects display.** `casefold()` improves matching but complicates prefix highlighting.

- **Deterministic ranking simplifies testing.** Static weight plus normalized alphabetical tie-breaks make output stable.

- **HTMX keeps the product small.** Server-rendered partials deliver interaction without turning the project into a frontend framework exercise.

- **Scope discipline matters.** It is better to document “no fuzzy matching” and “no cross-process invalidation” than to imply production-grade search behavior that is not implemented.

---

*Constitution v2.0 checklist: This document satisfies Article 5 (trade-off documentation), Article 6 (verification), and Article 7 (progressive complexity) for Search Autocomplete.*
