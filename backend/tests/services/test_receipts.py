from decimal import Decimal
from uuid import UUID

import pytest
from fastapi import BackgroundTasks

from app.errors import ForbiddenError, NotFoundError
from app.schemas.receipt import ReceiptCreate, ReceiptUpdate
from app.services.receipts import (
    create_receipt,
    image_path_belongs_to_group,
    list_receipts,
    retry_ocr,
    update_receipt,
)

RECEIPT_ID = UUID("11111111-1111-1111-1111-111111111111")
GROUP_ID = UUID("22222222-2222-2222-2222-222222222222")
OTHER_GROUP_ID = UUID("33333333-3333-3333-3333-333333333333")
UPLOADER_ID = UUID("44444444-4444-4444-4444-444444444444")


class _FakeQueryBuilder:
    def __init__(self, client, table_name):
        self._client = client
        self._table_name = table_name
        self._payload = None

    def update(self, payload):
        self._payload = payload
        return self

    def eq(self, *_args, **_kwargs):
        return self

    async def execute(self):
        return self._client.resolve(self._payload)


class _FakeAsyncClient:
    def __init__(self, matches: bool):
        """matches=False simulates the conditional .eq('ocr_status','failed')
        finding no rows — the fake doesn't model filters, it just returns
        empty/non-empty per this flag, since the service function's only
        observable behavior difference is 0 vs 1 rows returned."""
        self._matches = matches

    def table(self, name):
        return _FakeQueryBuilder(self, name)

    def resolve(self, payload):
        if not self._matches:
            return type("R", (), {"data": []})()
        row = {"id": str(RECEIPT_ID), "ocr_status": payload["ocr_status"], "ocr_error": payload["ocr_error"]}
        return type("R", (), {"data": [row]})()


async def test_retry_ocr_raises_not_found_when_receipt_not_currently_failed():
    client = _FakeAsyncClient(matches=False)
    with pytest.raises(NotFoundError):
        await retry_ocr(client, BackgroundTasks(), RECEIPT_ID)


async def test_retry_ocr_resets_status_and_queues_background_task():
    client = _FakeAsyncClient(matches=True)
    background_tasks = BackgroundTasks()

    result = await retry_ocr(client, background_tasks, RECEIPT_ID)

    assert result.ocr_status == "pending"
    assert result.ocr_error is None
    assert len(background_tasks.tasks) == 1


def test_image_path_belongs_to_group_accepts_matching_prefix():
    assert image_path_belongs_to_group(f"{GROUP_ID}/photo.jpg", GROUP_ID) is True


def test_image_path_belongs_to_group_rejects_a_different_groups_prefix():
    assert image_path_belongs_to_group(f"{OTHER_GROUP_ID}/photo.jpg", GROUP_ID) is False


def test_image_path_belongs_to_group_rejects_a_path_with_no_group_prefix():
    assert image_path_belongs_to_group("photo.jpg", GROUP_ID) is False


class _RejectingClient:
    """Fails the test if any DB call is attempted, proving the group check
    happens before any write — not merely alongside it — so a rejected
    receipt is never created and never reaches the service-role OCR
    pipeline."""

    def table(self, _name):
        raise AssertionError("create_receipt must reject a mismatched image_path before touching the database")


async def test_create_receipt_rejects_image_path_from_a_different_group():
    body = ReceiptCreate(image_path=f"{OTHER_GROUP_ID}/photo.jpg")

    with pytest.raises(ForbiddenError):
        await create_receipt(_RejectingClient(), BackgroundTasks(), GROUP_ID, UPLOADER_ID, body)


def _uuid(n: int) -> str:
    return f"00000000-0000-0000-0000-{n:012d}"


def _receipt_row(n: int, **overrides):
    base = {
        "id": _uuid(n),
        "group_id": str(GROUP_ID),
        "uploaded_by": str(UPLOADER_ID),
        "category_id": None,
        "merchant": "Kiwi",
        "total_amount": "20.00",
        "currency": "NOK",
        "receipt_date": "2026-01-01",
        "image_path": None,
        "created_at": "2026-01-01T00:00:00Z",
        "ocr_status": "succeeded",
        "is_done": False,
        "ocr_error": None,
    }
    base.update(overrides)
    return base


class _FakeListQueryBuilder:
    def __init__(self, client, table_name):
        self._client = client
        self._table_name = table_name

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def in_(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    async def execute(self):
        return type("R", (), {"data": self._client.data[self._table_name]})()


class _FakeListAsyncClient:
    """Ignores filter args entirely (same convention as the other fakes in
    this suite) — canned line_items must already be pre-filtered to only
    the shared-status rows, matching what the real .eq("status", "shared")
    query would return."""

    def __init__(self, *, receipts, line_items):
        self.data = {"receipts": receipts, "line_items": line_items}

    def table(self, name):
        return _FakeListQueryBuilder(self, name)


async def test_list_receipts_populates_shared_total_from_shared_line_items():
    receipts = [_receipt_row(1), _receipt_row(2)]
    shared_line_items = [
        {"receipt_id": _uuid(1), "total_price": "10.00"},
        {"receipt_id": _uuid(1), "total_price": "5.00"},
    ]
    client = _FakeListAsyncClient(receipts=receipts, line_items=shared_line_items)

    result = await list_receipts(client, GROUP_ID, None, None, None, None)

    by_id = {str(r.id): r for r in result}
    assert by_id[_uuid(1)].shared_total == Decimal("15.00")
    assert by_id[_uuid(2)].shared_total == Decimal(0)


class _FakeUpdateQueryBuilder:
    def __init__(self, client):
        self._client = client
        self._payload = None

    def update(self, payload):
        self._payload = payload
        return self

    def eq(self, *_args, **_kwargs):
        return self

    async def execute(self):
        merged = {**self._client.row, **self._payload}
        return type("R", (), {"data": [merged]})()


class _FakeUpdateAsyncClient:
    def __init__(self, row):
        self.row = row

    def table(self, _name):
        return _FakeUpdateQueryBuilder(self)


async def test_update_receipt_passes_is_done_through():
    client = _FakeUpdateAsyncClient(_receipt_row(1))

    result = await update_receipt(client, RECEIPT_ID, ReceiptUpdate(is_done=True))

    assert result.is_done is True
