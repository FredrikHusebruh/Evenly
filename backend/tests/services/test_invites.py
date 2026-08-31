from datetime import UTC, datetime, timedelta

import pytest

from app.errors import NotFoundError
from app.services.invites import check_invite_validity

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def make_invite(**overrides) -> dict:
    base = {
        "revoked_at": None,
        "expires_at": None,
        "max_uses": None,
        "use_count": 0,
    }
    base.update(overrides)
    return base


def test_valid_invite_passes():
    check_invite_validity(make_invite(), NOW)  # should not raise


def test_revoked_invite_rejected():
    invite = make_invite(revoked_at=NOW.isoformat())
    with pytest.raises(NotFoundError):
        check_invite_validity(invite, NOW)


def test_expired_invite_rejected():
    invite = make_invite(expires_at=(NOW - timedelta(days=1)).isoformat())
    with pytest.raises(NotFoundError):
        check_invite_validity(invite, NOW)


def test_not_yet_expired_invite_passes():
    invite = make_invite(expires_at=(NOW + timedelta(days=1)).isoformat())
    check_invite_validity(invite, NOW)  # should not raise


def test_invite_at_max_uses_rejected():
    invite = make_invite(max_uses=1, use_count=1)
    with pytest.raises(NotFoundError):
        check_invite_validity(invite, NOW)


def test_invite_under_max_uses_passes():
    invite = make_invite(max_uses=5, use_count=4)
    check_invite_validity(invite, NOW)  # should not raise


def test_invite_over_max_uses_rejected():
    invite = make_invite(max_uses=1, use_count=2)
    with pytest.raises(NotFoundError):
        check_invite_validity(invite, NOW)


def test_unlimited_uses_when_max_uses_is_none():
    invite = make_invite(max_uses=None, use_count=1000)
    check_invite_validity(invite, NOW)  # should not raise
