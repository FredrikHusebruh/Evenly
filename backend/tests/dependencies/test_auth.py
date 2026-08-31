from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from app.clients import jwt as jwt_client
from app.clients.jwt import verify_access_token


class _FakeSigningKey:
    def __init__(self, key) -> None:
        self.key = key


class _FakeJWKClient:
    def __init__(self, public_key) -> None:
        self._public_key = public_key

    def get_signing_key_from_jwt(self, token: str) -> _FakeSigningKey:
        return _FakeSigningKey(self._public_key)


@pytest.fixture
def keypair():
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key, private_key.public_key()


def _make_token(private_key, claims: dict) -> str:
    return jwt.encode(claims, private_key, algorithm="ES256")


def _patch_jwk_client(monkeypatch, public_key) -> None:
    monkeypatch.setattr(jwt_client, "get_jwk_client", lambda: _FakeJWKClient(public_key))


def _base_claims(**overrides) -> dict:
    now = datetime.now(UTC)
    claims = {
        "sub": str(uuid4()),
        "email": "user@example.com",
        "aud": "authenticated",
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "iat": int(now.timestamp()),
    }
    claims.update(overrides)
    return claims


def test_valid_token_is_verified(monkeypatch, keypair):
    private_key, public_key = keypair
    _patch_jwk_client(monkeypatch, public_key)

    claims = _base_claims()
    token = _make_token(private_key, claims)

    result = verify_access_token(token)
    assert result["sub"] == claims["sub"]
    assert result["email"] == "user@example.com"


def test_expired_token_is_rejected(monkeypatch, keypair):
    private_key, public_key = keypair
    _patch_jwk_client(monkeypatch, public_key)

    now = datetime.now(UTC)
    claims = _base_claims(
        exp=int((now - timedelta(hours=1)).timestamp()),
        iat=int((now - timedelta(hours=2)).timestamp()),
    )
    token = _make_token(private_key, claims)

    with pytest.raises(jwt.ExpiredSignatureError):
        verify_access_token(token)


def test_wrong_audience_is_rejected(monkeypatch, keypair):
    private_key, public_key = keypair
    _patch_jwk_client(monkeypatch, public_key)

    token = _make_token(private_key, _base_claims(aud="not-authenticated"))

    with pytest.raises(jwt.InvalidAudienceError):
        verify_access_token(token)


def test_token_signed_by_different_key_is_rejected(monkeypatch, keypair):
    _, public_key = keypair
    other_private_key = ec.generate_private_key(ec.SECP256R1())
    _patch_jwk_client(monkeypatch, public_key)

    token = _make_token(other_private_key, _base_claims())

    with pytest.raises(jwt.InvalidSignatureError):
        verify_access_token(token)


def test_missing_sub_claim_is_rejected(monkeypatch, keypair):
    private_key, public_key = keypair
    _patch_jwk_client(monkeypatch, public_key)

    claims = _base_claims()
    del claims["sub"]
    token = _make_token(private_key, claims)

    with pytest.raises(jwt.MissingRequiredClaimError):
        verify_access_token(token)
