from uuid import UUID

import pytest

from app.errors import ValidationError
from app.schemas.line_item import LineItemUpdate
from app.services.line_items import update_line_item

LINE_ITEM_ID = UUID("11111111-1111-1111-1111-111111111111")
RECEIPT_ID = UUID("22222222-2222-2222-2222-222222222222")
GROUP_ID = UUID("33333333-3333-3333-3333-333333333333")
MEMBER_ID = UUID("44444444-4444-4444-4444-444444444444")
NON_MEMBER_ID = UUID("55555555-5555-5555-5555-555555555555")


class _FakeQueryBuilder:
    def __init__(self, client, table_name):
        self._client = client
        self._table_name = table_name
        self._filters: dict[str, str] = {}
        self._maybe_single = False
        self._update_payload = None

    def select(self, *_args, **_kwargs):
        return self

    def update(self, payload):
        self._update_payload = payload
        return self

    def eq(self, key, value):
        self._filters[key] = value
        return self

    def maybe_single(self):
        self._maybe_single = True
        return self

    async def execute(self):
        return self._client.resolve(self._table_name, self._filters, self._update_payload, self._maybe_single)


class _FakeAsyncClient:
    """Models just enough of the line_items/receipts/group_members chain that
    `_validate_personal_assignment` and `update_line_item` touch."""

    def __init__(self, *, line_item: dict, receipt: dict, member_exists: bool):
        self._line_item = line_item
        self._receipt = receipt
        self._member_exists = member_exists

    def table(self, name):
        return _FakeQueryBuilder(self, name)

    def resolve(self, table_name, filters, update_payload, maybe_single):
        if update_payload is not None:
            merged = {**self._line_item, **update_payload}
            return type("R", (), {"data": [merged]})()
        if table_name == "line_items":
            return type("R", (), {"data": self._line_item})() if maybe_single else None
        if table_name == "receipts":
            return type("R", (), {"data": self._receipt})() if maybe_single else None
        if table_name == "group_members":
            if not self._member_exists:
                return None
            return type("R", (), {"data": {"user_id": filters.get("user_id")}})()
        raise AssertionError(f"unexpected table {table_name}")


def _line_item(**overrides):
    base = {
        "id": str(LINE_ITEM_ID),
        "receipt_id": str(RECEIPT_ID),
        "description": "Test item",
        "quantity": "1",
        "unit_price": "10.00",
        "total_price": "10.00",
        "created_at": "2026-01-01T00:00:00Z",
        "status": "shared",
        "assigned_to": None,
    }
    base.update(overrides)
    return base


def _receipt():
    return {"group_id": str(GROUP_ID)}


async def test_update_rejects_personal_status_with_no_assignee():
    client = _FakeAsyncClient(line_item=_line_item(), receipt=_receipt(), member_exists=True)

    with pytest.raises(ValidationError):
        await update_line_item(client, LINE_ITEM_ID, LineItemUpdate(status="personal"))


async def test_update_rejects_personal_status_assigned_to_a_non_member():
    client = _FakeAsyncClient(line_item=_line_item(), receipt=_receipt(), member_exists=False)

    with pytest.raises(ValidationError):
        await update_line_item(client, LINE_ITEM_ID, LineItemUpdate(status="personal", assigned_to=NON_MEMBER_ID))


async def test_update_accepts_personal_status_with_a_valid_member():
    client = _FakeAsyncClient(line_item=_line_item(), receipt=_receipt(), member_exists=True)

    result = await update_line_item(client, LINE_ITEM_ID, LineItemUpdate(status="personal", assigned_to=MEMBER_ID))

    assert result.status == "personal"
    assert result.assigned_to == MEMBER_ID


async def test_update_reuses_existing_assignee_when_only_status_changes():
    client = _FakeAsyncClient(
        line_item=_line_item(status="shared", assigned_to=str(MEMBER_ID)), receipt=_receipt(), member_exists=True
    )

    result = await update_line_item(client, LINE_ITEM_ID, LineItemUpdate(status="personal"))

    assert result.status == "personal"
    assert result.assigned_to == MEMBER_ID


async def test_update_rejects_reassigning_an_existing_personal_item_to_a_non_member():
    client = _FakeAsyncClient(
        line_item=_line_item(status="personal", assigned_to=str(MEMBER_ID)), receipt=_receipt(), member_exists=False
    )

    with pytest.raises(ValidationError):
        await update_line_item(client, LINE_ITEM_ID, LineItemUpdate(assigned_to=NON_MEMBER_ID))


async def test_update_skips_assignment_validation_for_non_personal_status():
    client = _FakeAsyncClient(line_item=_line_item(), receipt=_receipt(), member_exists=False)

    result = await update_line_item(client, LINE_ITEM_ID, LineItemUpdate(status="excluded"))

    assert result.status == "excluded"
