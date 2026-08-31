from functools import lru_cache
from typing import Any

from postgrest.base_request_builder import SingleAPIResponse
from supabase import AsyncClient, create_async_client

from app.config import get_settings


def unwrap_maybe_single(res: SingleAPIResponse | None) -> dict[str, Any] | None:
    """postgrest-py's `.maybe_single().execute()` returns None outright (not
    a response object with `.data=None`) when zero rows match — normalize
    that here so callers can just check truthiness of a dict."""
    return res.data if res is not None else None


@lru_cache
def _service_client_singleton() -> "SupabaseSingleton":
    return SupabaseSingleton()


class SupabaseSingleton:
    """Lazily-created, cached async client instances (one per key scope).

    Client creation is itself async, so we can't just @lru_cache the coroutine
    result directly — this wrapper caches the created client after the first
    await instead.
    """

    def __init__(self) -> None:
        self._service_client: AsyncClient | None = None
        self._anon_client: AsyncClient | None = None

    async def service(self) -> AsyncClient:
        if self._service_client is None:
            settings = get_settings()
            self._service_client = await create_async_client(settings.supabase_url, settings.supabase_service_role_key)
        return self._service_client

    async def anon(self) -> AsyncClient:
        if self._anon_client is None:
            settings = get_settings()
            self._anon_client = await create_async_client(settings.supabase_url, settings.supabase_anon_key)
        return self._anon_client


async def get_service_client() -> AsyncClient:
    """Service-role client — bypasses RLS. Only for cases RLS structurally
    can't apply: the OCR background task (no live user session) and invite
    redemption/preview (the requester isn't a group member yet, and a code's
    validity isn't expressible as a row-security predicate). Any
    authorization it skips must be enforced explicitly in the calling
    service.
    """
    return await _service_client_singleton().service()


async def get_anon_client() -> AsyncClient:
    """Anon-key client for user-independent work. Cached singleton."""
    return await _service_client_singleton().anon()


async def create_request_client(access_token: str) -> AsyncClient:
    """A fresh, non-cached client scoped to one request's caller session.

    Never share/cache this across requests — the token is set on the
    postgrest sub-client's auth state, so a shared instance would race under
    concurrent requests from different users.
    """
    settings = get_settings()
    client = await create_async_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(access_token)
    return client
