from functools import lru_cache

import jwt

from app.config import get_settings


@lru_cache
def get_jwk_client() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(get_settings().supabase_jwt_jwks_url)


def verify_access_token(token: str) -> dict:
    """Verify a Supabase Auth access token signed with the project's ES256 key.

    Raises jwt.PyJWTError (or a subclass) on any invalid/expired/malformed token.
    """
    signing_key = get_jwk_client().get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256"],
        audience="authenticated",
        options={"require": ["exp", "sub"]},
    )
