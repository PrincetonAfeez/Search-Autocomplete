# Architecture

## Problem

Serve ranked prefix suggestions over a searchable corpus with:

- exact, case-insensitive prefix matching
- static weight-based ranking
- safe HTML rendering and a thin web UI

## System map

```mermaid
flowchart LR
    Browser["Browser / HTMX"] --> Views["web.views"]
    CLI["cli.py"] --> Loader["corpus.loader"]
    Views --> Loader
    Loader --> Engine["AutocompleteEngine"]
    Engine --> Trie["Trie"]
    Loader --> DB[("SQLite Word rows")]
    Admin["Django admin"] --> DB
    Seed["seed_corpus"] --> DB
    DB -. signals .-> Loader
```

## Layer responsibilities

| Layer | Role |
| --- | --- |
| `autocomplete/` | Pure Python trie, normalizer, engine. No Django imports. |
| `corpus/` | `Word` model, loader singleton, cache invalidation, management commands. |
| `web/` | GET-only views, HTMX partials, keyboard navigation. |
| `cli.py` | Optional REPL / one-shot queries via Django-backed loader. |

## Request flow (type `py`)

```mermaid
sequenceDiagram
    participant U as User
    participant H as HTMX
    participant V as suggest view
    participant L as corpus.loader
    participant E as AutocompleteEngine
    participant T as Trie

    U->>H: keyup "py"
    H->>V: GET /suggest/?q=py
    V->>L: get_engine()
    L->>E: suggest("py")
    E->>T: collect_top_k("py", 10)
    T-->>E: ranked suggestions
    E-->>V: Suggestion list
    V-->>H: suggestions.html partial
    H-->>U: DOM swap
```

## Dependency direction

```text
web -> corpus.loader -> autocomplete
corpus -> autocomplete
cli -> corpus.loader -> autocomplete
```

See ADRs in [`docs/adr/`](adr/) for trade-offs (singleton engine, cache invalidation, security posture).
