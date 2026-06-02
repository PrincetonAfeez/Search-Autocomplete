# ADR 0007: Security Posture

## Decision

Document the project's explicit security posture so a reader does not have to
infer it from the middleware list.

## What the app does

- Reads `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` from environment variables
  with development-only defaults (`config/settings.py`).
- Enables Django's standard security middleware: `SecurityMiddleware`,
  `SessionMiddleware`, `CommonMiddleware`, `CsrfViewMiddleware`,
  `AuthenticationMiddleware`, `MessageMiddleware`, and
  `XFrameOptionsMiddleware` (clickjacking protection).
- HTML autoescapes all template variables, so suggestion display + prefix
  highlighting are safe against XSS for arbitrary corpus text.
- Caps user queries at 255 characters via `MAX_TERM_LENGTH` in
  `autocomplete/constants.py`, enforced in `AutocompleteEngine.suggest()` and
  truncated in `web/views.py` before rendering.
- Validates corpus input: `Word.text` ≤ 255 chars; normalized text after
  casefold must also fit in 255 chars; `weight ≥ 0` enforced at the field,
  validator, and DB constraint level.
- Django admin (`/admin/`) requires authenticated staff users.

## What the app does NOT do

- **No authentication on `/search/` or `/suggest/`** — they are intentionally
  public read-only endpoints.
- **No rate limiting** — a single client can drive the `/suggest/` endpoint
  as fast as the worker serves. Acceptable for a single-user dev deployment;
  not safe to expose to the open internet.
- **No CSRF on `/suggest/`** — the endpoint is `GET`-only via `@require_GET`,
  so CSRF is not applicable.
- **No input sanitization beyond Django's autoescape** — corpus text is
  trusted (it is operator-supplied via `seed_corpus` or admin); user query
  strings are only used to walk the trie, never executed or rendered raw.
- **No secrets management** — `SECRET_KEY` falls back to a clearly-labeled
  `django-insecure-…` default for local dev. Production deployments must set
  `DJANGO_SECRET_KEY` and `DJANGO_DEBUG=0`.
- **No HTTPS configuration** — handled by the deployment layer, which is
  out of scope (see ADR 0001).
- **No content security policy (CSP)** — relies on Django's default headers.

## Trade-off

The app is shaped for single-user academic deployment behind `runserver` on
`localhost`. Anything beyond that requires the operator to add their own
rate limiting, secrets management, and TLS — none of which is the project's
purpose.
