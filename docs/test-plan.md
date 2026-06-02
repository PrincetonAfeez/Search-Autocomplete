# Test plan

Requirement traceability for graders and reviewers.

| Requirement | Test(s) | Layer |
| --- | --- | --- |
| Trie insert/lookup/delete | `tests/test_trie.py` | core |
| Casefold + display match length | `tests/test_normalizer.py` | core |
| Engine ranking, limits, truncation | `tests/test_engine.py` | core |
| No Django in autocomplete | `tests/test_core_guardrails.py` | core |
| Trie random invariants | `tests/test_trie_fuzz.py` | core |
| Lazy engine singleton | `tests/test_loader.py` | corpus |
| Signal + queryset cache invalidation | `tests/test_loader.py` | corpus |
| Word model validation | `tests/test_corpus_model.py` | corpus |
| seed_corpus import/dry-run | `tests/test_seed_command.py` | corpus |
| Admin batch actions | `tests/test_admin.py` | corpus |
| rebuild_trie command | `tests/test_rebuild_trie.py` | corpus |
| Suggest view states + highlighting | `tests/test_web_views.py` | web |
| Root redirect, long query | `tests/test_urls.py` | web |
| Cache-Control on suggest | `tests/test_web_views.py` | web |
| CLI REPL / flags | `tests/test_cli.py` | cli |
| Settings env validation | `tests/test_settings.py` | config |
| Browser suggest smoke | `tests/test_e2e_playwright.py` | e2e |
| Suggest latency budget | `tests/test_performance.py` | perf |

Run all: `python -m pytest`  
With coverage: `make coverage` or `.\tasks.ps1 coverage`
