# Security

## Secrets
- Never commit `.env` files or hardcode secrets/keys/URLs; `.env` is always gitignored and secrets are read only through the settings layer (see [architecture.md](architecture.md) for the settings-object pattern).
- Service-role / admin keys stay server-side only; the frontend must never receive them. Service-role keys also bypass Row Level Security — see [supabase.md](supabase.md) for what that implies for authorization.
- In Vite projects, only env vars prefixed `VITE_` reach the browser bundle — never give a secret that prefix.

## Input & errors
- Validate every external input through a schema at the boundary.
- Authorization decisions check server-side state (DB/auth provider), never client-supplied claims.
- Don't leak internals in API error responses: return a generic message/status to the client and log the real exception server-side. Never return raw stack traces or exception messages.

## Frontend
- Never render unsanitized data via `dangerouslySetInnerHTML` or other raw-HTML injection; rely on the framework's default escaping.
- Avoid storing session/access tokens in `localStorage`/`sessionStorage` where possible — an XSS bug becomes a stolen session. Prefer httpOnly cookies.

## Deployment
- Before deploying past local dev, configure CORS with an explicit allowed-origins list — never a wildcard `*`.

## Auth
- Never grant privileges (membership, roles, invitations) from a hook/trigger that fires on user *signup* alone — signup fires before email confirmation, so anyone can claim privileges meant for another address by signing up with it. Gate privilege-granting logic on confirmed email (handle both auto-confirm and confirm-by-link flows). This applies directly to Supabase Auth triggers — see [supabase.md](supabase.md).

See also: [engineering-principles.md](engineering-principles.md#never-trust-data-crossing-a-boundary) for the boundary-validation rule this section enforces in practice.
