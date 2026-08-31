from uuid import UUID

import pytest
from fastapi import BackgroundTasks

from app.errors import NotFoundError
from app.services.receipts import retry_ocr

RECEIPT_ID = UUID("11111111-1111-1111-1111-111111111111")


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
