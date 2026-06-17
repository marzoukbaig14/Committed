# HTTP Contract — Committed inference service

This is the seam between the Committed backend (this repo) and the portfolio frontend
(the separate Next.js/Vercel repo). It is locked by **ADR 0043**. The backend owns this
contract; **once set, it does not change without telling the frontend agent**, so the two
stay in sync.

Base URL: the Hugging Face **Docker** Space hosting `committed.serving.api`.

## `POST /generate`

Generate one Conventional Commits subject line from a unified diff.

**Request** — `application/json`

```json
{ "diff": "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n" }
```

**Response** — `200 application/json`

```json
{ "message": "fix(app): set x to 2" }
```

- `message` is a single line, already normalized, and **grammar-valid by construction**:
  `type(scope)?: description`, lowercase type from the ten-code set
  (`feat fix refactor docs test chore perf style build ci`), optional `(scope)`, no
  breaking-change `!`, no trailing period (ADR 0039).

**Errors**

| Status | When                         | Body                                  |
|--------|------------------------------|---------------------------------------|
| 400    | `diff` empty / whitespace    | `{"detail": "empty diff"}`            |
| 422    | `diff` missing / wrong type  | FastAPI validation error              |
| 503    | model not loaded yet         | `{"detail": "model not loaded"}`      |

## `GET /health`

```json
{ "status": "ok" }
```

Returns `200` once the model is loaded. The frontend pings this on page load to wake the
Space early and to drive a "waking up" state. The free Docker Space sleeps after ~48 h idle;
while it cold-starts, requests fail or hang until the container is up and the model is
loaded, after which `/health` returns `200`. Poll it to detect readiness.

## CORS

The service allows the portfolio's browser origins:

- exact production and custom domains — set via the `COMMITTED_CORS_ORIGINS` env var
  (comma-separated) at deploy time;
- all Vercel preview deployments — `https://*.vercel.app`, matched by regex in `api.py`.

Allowed methods: `GET, POST, OPTIONS`. Without this, the browser blocks the call from the page.

## Model swap (backend note)

The served model is selected by environment variable and is never hardcoded. Setting
`COMMITTED_MODEL_PATH` to the fine-tuned `.gguf` swaps it in with no code change; the default
is the pinned baseline (ADR 0038). The contract above is unchanged by the swap.
