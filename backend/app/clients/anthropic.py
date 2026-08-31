from functools import lru_cache

from anthropic import AsyncAnthropic

from app.config import get_settings


@lru_cache
def get_anthropic_client() -> AsyncAnthropic | None:
    """Cached Anthropic client, or None if ANTHROPIC_API_KEY isn't configured.

    Uses an explicit api_key rather than the SDK's ambient env-var fallback
    so backend behavior never depends on the host machine's local Anthropic
    CLI/profile state — OCR is either configured via this one setting or
    treated as unconfigured.
    """
    settings = get_settings()
    if not settings.anthropic_api_key:
        return None
    return AsyncAnthropic(api_key=settings.anthropic_api_key)
