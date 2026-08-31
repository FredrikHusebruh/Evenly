# Testing

- **Backend (Python):** use `pytest`, mirroring the app package layout under `tests/`. Run it through `uv run pytest` — see [tooling.md](tooling.md) for the `uv`-first workflow.
- **Frontend (Vite-based):** use Vitest with React Testing Library — it shares Vite's config and transform pipeline, so no separate bundler setup.
- Don't add a test suite or test dependencies speculatively — wait until there's actual behavior worth covering, then set it up properly.

See also: [supabase.md](supabase.md) for the client-scope patterns worth covering once Supabase-backed services have real behavior.
