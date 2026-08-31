# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@.claude/rules/engineering-principles.md
@.claude/rules/architecture.md
@.claude/rules/security.md
@.claude/rules/supabase.md
@.claude/rules/testing.md
@.claude/rules/tooling.md

## Project overview

Evenly is a receipt-splitting app. The repo root is the app root (not nested) and holds three parts:

- `supabase/` — Postgres schema (migrations) for a **Supabase Cloud** project, no local app code
- `backend/` — FastAPI API, managed with `uv`
- `frontend/` — Vite + React + TypeScript + Tailwind v4

The root `package.json` exists only to host the `supabase` CLI as a devDependency (`npx supabase ...`); it is not an application package.

## Commands

### Backend (`backend/`)
```
uv run fastapi dev app/main.py --port 8010   # dev server at http://127.0.0.1:8010, docs at /docs
uv add <package>                 # add a dependency
uv sync                          # install locked dependencies
```
No test suite or linter is configured yet in `backend/`.

### Frontend (`frontend/`)
```
npm run dev       # dev server at http://localhost:5173
npm run build      # tsc -b && vite build
npm run lint       # oxlint (not eslint) — config in .oxlintrc.json
npm run preview
```
No test suite is configured yet in `frontend/`.

### Supabase (root)
```
npx supabase db push                            # apply supabase/migrations/*.sql to the linked cloud project
npx supabase migration new <name>                # create a new migration file
npx supabase link --project-ref <ref>            # (re)link this repo to a Supabase Cloud project
npx supabase projects api-keys --project-ref <ref>  # fetch anon/service_role keys for a project
```
This project intentionally does **not** use the local Docker Supabase stack (`supabase start`) — local dev points directly at a real Supabase Cloud project. Don't reintroduce `supabase start`/local Docker workflows unless explicitly asked.

## Architecture

**Auth model:** Supabase Auth on this project signs tokens with **ES256 asymmetric keys**, not the legacy HS256 shared secret. There is no static JWT secret to configure — `backend/.env` holds `SUPABASE_JWT_JWKS_URL` (the project's `/auth/v1/.well-known/jwks.json` endpoint) instead of `SUPABASE_JWT_SECRET`. Verify incoming tokens with PyJWT's `jwt.PyJWKClient(jwks_url)` and `algorithms=["ES256"]` — a static-secret `jwt.decode(token, secret, algorithms=["HS256"])` approach will not work against this project.

**Frontend ↔ backend:** the frontend signs in via `@supabase/supabase-js`, takes `session.access_token`, and calls the backend as `Authorization: Bearer <token>`. In dev, `frontend/vite.config.ts` proxies `/api` to `http://127.0.0.1:8010` (not the usual 8000 — that port is stuck with an orphaned listener on the dev machine with no killable owning process, confirmed via `netstat`/`Get-NetTCPConnection`/Docker), so frontend code calls relative `/api/v1/...` paths and there's no CORS handling needed locally. If 8000 frees up again (e.g. after a reboot), both `vite.config.ts`'s proxy target and the backend's `--port` flag can move back.

**Env vars:**
- `backend/.env`: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (full-access, backend-only), `SUPABASE_JWT_JWKS_URL`, `ANTHROPIC_API_KEY` (optional — OCR-specific; the app boots and every other feature works without it, OCR just degrades to "add items manually")
- `frontend/.env.local`: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` — anon key only, `service_role` must never be exposed to the frontend

**Data model** (`supabase/migrations/20260831125841_initial_schema.sql`):
- `groups`, `group_members` (join table with `role`), `categories`, `receipts`, `line_items`, `item_assignments`
- Users are Supabase Auth users (`auth.users`); every other table is scoped to group membership
- RLS on every table is enforced through a `public.is_group_member(group_id)` `SECURITY DEFINER` helper function rather than repeating the membership subquery per policy
- A private `receipts` storage bucket stores receipt images, with per-group access enforced by treating the first path segment of the object name as the group id (`storage.foldername(name)[1]::uuid`) — so receipt images must be uploaded under a `<group_id>/...` path

**OCR pipeline** (`backend/app/services/ocr/`): a background task (`pipeline.process_receipt_ocr`, kicked off via FastAPI `BackgroundTasks` right after a receipt is created) downloads the receipt image from Storage and sends it to Claude's vision API (`claude_provider.ClaudeVisionOcrProvider`, model `claude-sonnet-5`) with a Norwegian-receipt-tuned prompt (`prompts.py`) via **forced tool-use** so the response is always structured JSON, not free-form prose. `OcrProvider` (`provider.py`) is a `Protocol`, so the Claude implementation is swappable. With no `ANTHROPIC_API_KEY` configured, `clients/anthropic.py::get_anthropic_client()` returns `None` and every receipt lands on `ocr_status='failed'` with a safe "add items manually" message — the app boots and works fine either way; OCR is the only thing that degrades. `POST /api/v1/receipts/{id}/retry-ocr` re-queues a failed receipt.

