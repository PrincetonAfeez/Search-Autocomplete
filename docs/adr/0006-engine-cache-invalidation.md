# ADR 0006: Engine Cache Invalidation

## Decision

Invalidate the in-process autocomplete engine via Django `post_save` and
`post_delete` signals on the `Word` model, plus an explicit `clear_engine()`
call at the end of the `seed_corpus` management command.

The seed command also detaches the per-row `post_save` receiver for the
duration of its bulk loop and clears once at the end.

## Reason

The engine is a lazy process-level singleton built from active `Word` rows
(see [ADR 0001](0001-process-level-trie-singleton.md)). Without
invalidation, an edit through the admin or `python manage.py shell` would
not be visible until the worker restarted. Wiring the post-save signal makes
the cache self-healing for the single-process case.

Disconnecting the receiver during bulk seeds avoids `O(N)` lock cycles
during what is conceptually a single batch operation.

## Trade-off

- Multi-worker deployments still need a per-worker rebuild (`manage.py
  rebuild_trie` or restart). Cross-process invalidation is out of scope.
- Admin bulk actions that call `QuerySet.update()` or `QuerySet.delete()`
  bypass signals. `WordAdmin` calls `clear_engine()` explicitly after
  activate/deactivate and bulk delete. `Word.objects.update()`, `bulk_update()`,
  and `bulk_create()` clear the cache via `WordQuerySet`.
- The signal fires inside the same transaction as the write. A rollback
  invalidates a still-valid cache, forcing one redundant rebuild on the
  next read. We accept this — the cost is small and the alternative (post-
  commit hooks) adds complexity for the academic scope.
- `seed_corpus` deliberately detaches both `post_save` and `post_delete`
  during its bulk loop and re-attaches them on exit (success or exception).
  This keeps `--clear` / large seeds at O(1) invalidations rather than O(N).
