# Architecture & layering

- Keep an MVC-style separation even in API-only or SPA codebases:
  - **Backend:** models (domain/DB-shaped data) → schemas (typed request/response shapes over the wire — never raw `dict`s) → routers/controllers (parse, validate, delegate, respond — skinny, no business logic) → services (all business logic, one module per domain concern).
  - **Frontend:** components render (View); custom hooks hold state and side-effects (Controller); plain types plus API-fetching code define and load data shapes (Model). Never mix data-fetching/business logic into a component that also renders a large UI tree.
- Read configuration through a single cached settings object (e.g. pydantic `Settings` behind `get_settings()`) — never `os.environ` scattered through the codebase. Secrets flow through this same layer; see [security.md](security.md#secrets).
- Centralize external-client creation (DB, Supabase, HTTP APIs) in one module with explicit factories; never instantiate clients ad hoc at call sites. For Supabase specifically, see [supabase.md](supabase.md) for which client scope (anon vs. per-request vs. service role) to hand out.

See also: [engineering-principles.md](engineering-principles.md) for the single-responsibility and composition rules this layering follows from.
