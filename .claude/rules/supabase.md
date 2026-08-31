# Supabase

- Be deliberate about which key each client uses (anon vs. service role) and what that implies: a service-role key bypasses Row Level Security, so any authorization it skips must be enforced explicitly in the service layer instead. See [security.md](security.md#secrets) for why the service-role key must never reach the frontend.
- Prefer enforcing data-access rules with RLS policies over ad-hoc filtering in application code, so authorization doesn't depend on every call site remembering to filter.
- Use two client scopes: a cached, anon-key client for user-independent work (e.g. token validation), and a per-request client scoped to the caller's session for anything RLS-protected. Create both through the centralized client-factory module described in [architecture.md](architecture.md).
- Never grant privileges from a signup-only trigger — gate on confirmed email. See [security.md](security.md#auth) for the full rule and why.

See also: [testing.md](testing.md) for how Supabase-backed services should still be covered with `pytest`/Vitest once there's real behavior to test.
