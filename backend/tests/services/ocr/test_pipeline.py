from datetime import date
from decimal import Decimal

import pytest

from app.services.ocr import pipeline as pipeline_module
from app.services.ocr.pipeline import (
    _SAFE_ERROR_MESSAGE,
    build_receipt_patch,
    guess_image_mime_type,
    match_category_id,
    process_receipt_ocr,
    run_ocr_pipeline,
)
from app.services.ocr.provider import OcrProviderError, ParsedLineItem, ParsedReceipt

RECEIPT_ID = "11111111-1111-1111-1111-111111111111"


# --- fakes -------------------------------------------------------------


class _FakeSingleResult:
    def __init__(self, data):
        self.data = data


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQueryBuilder:
    def __init__(self, client, table_name):
        self._client = client
        self._table_name = table_name
        self._operation = None
        self._payload = None
        self._is_single = False

    def select(self, *_args, **_kwargs):
        self._operation = "select"
        return self

    def update(self, payload):
        self._operation = "update"
        self._payload = payload
        return self

    def insert(self, payload):
        self._operation = "insert"
        self._payload = payload
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def maybe_single(self):
        self._is_single = True
        return self

    async def execute(self):
        self._client.calls.append((self._table_name, self._operation, self._payload))
        return self._client.resolve(self._table_name, self._operation, self._payload, self._is_single)


class _FakeStorageBucket:
    def __init__(self, image_bytes=b"fake-image-bytes"):
        self.image_bytes = image_bytes
        self.downloaded_paths = []

    def from_(self, _bucket):
        return self

    async def download(self, path):
        self.downloaded_paths.append(path)
        return self.image_bytes


class _FakeAsyncClient:
    def __init__(self, receipt, categories=None):
        self.calls = []
        self._receipt = dict(receipt)
        self._categories = categories or []
        self.storage = _FakeStorageBucket()

    def table(self, name):
        return _FakeQueryBuilder(self, name)

    def resolve(self, table_name, operation, payload, is_single):
        if table_name == "receipts":
            if operation == "update":
                self._receipt.update(payload)
                return _FakeResult([dict(self._receipt)])
            if operation == "select":
                return _FakeSingleResult(dict(self._receipt)) if is_single else _FakeResult([dict(self._receipt)])
        if table_name == "categories" and operation == "select":
            return _FakeResult(self._categories)
        if table_name == "line_items" and operation == "insert":
            return _FakeResult(payload)
        raise AssertionError(f"unexpected fake call: {table_name}.{operation}")


class _FakeOcrProvider:
    def __init__(self, parsed=None, exception=None):
        self._parsed = parsed
        self._exception = exception
        self.call_count = 0

    async def extract_receipt(self, _image_bytes, _mime_type):
        self.call_count += 1
        if self._exception:
            raise self._exception
        return self._parsed


def make_receipt(**overrides):
    base = {
        "id": RECEIPT_ID,
        "group_id": "22222222-2222-2222-2222-222222222222",
        "image_path": f"{RECEIPT_ID}/photo.jpg",
        "merchant": None,
        "receipt_date": None,
        "total_amount": None,
        "category_id": None,
    }
    base.update(overrides)
    return base


def make_parsed(**overrides):
    base = {
        "merchant": "Rema 1000",
        "receipt_date": date(2026, 3, 14),
        "total_amount": Decimal("149.50"),
        "suggested_category": "Dagligvarer",
        "line_items": [
            ParsedLineItem(description="Melk", quantity=Decimal(1), unit_price=Decimal("24.90"), total_price=Decimal("24.90"))
        ],
    }
    base.update(overrides)
    return ParsedReceipt(**base)


# --- guess_image_mime_type ----------------------------------------------


def test_guess_image_mime_type_recognizes_common_extensions():
    assert guess_image_mime_type("group/photo.jpg") == "image/jpeg"
    assert guess_image_mime_type("group/photo.png") == "image/png"


def test_guess_image_mime_type_falls_back_to_jpeg_for_unknown_extension():
    assert guess_image_mime_type("group/photo.heic") == "image/jpeg"
    assert guess_image_mime_type("group/photo") == "image/jpeg"


# --- match_category_id ----------------------------------------------------


def test_match_category_id_exact_match():
    categories = [{"id": "c1", "name": "Dagligvarer"}, {"id": "c2", "name": "Snacks"}]
    assert match_category_id(categories, "Dagligvarer") == "c1"


def test_match_category_id_case_insensitive():
    categories = [{"id": "c1", "name": "Dagligvarer"}]
    assert match_category_id(categories, "dagligvarer") == "c1"


def test_match_category_id_no_match_returns_none():
    categories = [{"id": "c1", "name": "Dagligvarer"}]
    assert match_category_id(categories, "Alkohol") is None


def test_match_category_id_none_suggestion_returns_none():
    assert match_category_id([{"id": "c1", "name": "Dagligvarer"}], None) is None


def test_match_category_id_empty_categories_returns_none():
    assert match_category_id([], "Dagligvarer") is None


# --- build_receipt_patch ----------------------------------------------------


def test_build_receipt_patch_fills_all_null_fields():
    receipt = make_receipt()
    parsed = make_parsed()
    patch = build_receipt_patch(receipt, parsed, category_id="c1")

    assert patch["ocr_status"] == "succeeded"
    assert patch["merchant"] == "Rema 1000"
    assert patch["receipt_date"] == "2026-03-14"
    assert patch["total_amount"] == "149.50"
    assert patch["category_id"] == "c1"


def test_build_receipt_patch_never_overwrites_existing_values():
    receipt = make_receipt(merchant="Already Set", receipt_date="2020-01-01", total_amount="1.00", category_id="existing")
    parsed = make_parsed()
    patch = build_receipt_patch(receipt, parsed, category_id="c1")

    assert "merchant" not in patch
    assert "receipt_date" not in patch
    assert "total_amount" not in patch
    assert "category_id" not in patch
    assert patch == {"ocr_status": "succeeded"}


# --- run_ocr_pipeline -----------------------------------------------------


async def test_run_ocr_pipeline_success_sequence():
    client = _FakeAsyncClient(make_receipt(), categories=[{"id": "c1", "name": "Dagligvarer"}])
    provider = _FakeOcrProvider(parsed=make_parsed())

    await run_ocr_pipeline(RECEIPT_ID, client, provider)

    operations = [(table, op) for table, op, _ in client.calls]
    assert operations == [
        ("receipts", "update"),  # -> processing
        ("receipts", "select"),  # fetch receipt
        ("categories", "select"),  # category lookup
        ("line_items", "insert"),
        ("receipts", "update"),  # -> succeeded + patch
    ]
    assert client.storage.downloaded_paths == [make_receipt()["image_path"]]
    assert provider.call_count == 1
    assert client._receipt["ocr_status"] == "succeeded"
    assert client._receipt["merchant"] == "Rema 1000"


async def test_run_ocr_pipeline_with_no_line_items_still_succeeds():
    client = _FakeAsyncClient(make_receipt())
    provider = _FakeOcrProvider(parsed=make_parsed(line_items=[], suggested_category=None))

    await run_ocr_pipeline(RECEIPT_ID, client, provider)

    operations = [(table, op) for table, op, _ in client.calls]
    assert ("line_items", "insert") not in operations
    assert client._receipt["ocr_status"] == "succeeded"


async def test_run_ocr_pipeline_propagates_provider_error_without_inserting_items():
    client = _FakeAsyncClient(make_receipt())
    provider = _FakeOcrProvider(exception=OcrProviderError("boom"))

    with pytest.raises(OcrProviderError):
        await run_ocr_pipeline(RECEIPT_ID, client, provider)

    operations = [(table, op) for table, op, _ in client.calls]
    assert ("line_items", "insert") not in operations
    assert ("receipts", "update") in operations  # the processing-status update did happen


# --- process_receipt_ocr ---------------------------------------------------


async def test_process_receipt_ocr_marks_failed_with_safe_message_on_provider_error(monkeypatch):
    client = _FakeAsyncClient(make_receipt())
    provider = _FakeOcrProvider(exception=OcrProviderError("some internal detail that must not leak"))

    async def fake_get_service_client():
        return client

    monkeypatch.setattr(pipeline_module, "get_service_client", fake_get_service_client)
    monkeypatch.setattr(pipeline_module, "get_ocr_provider", lambda: provider)

    await process_receipt_ocr(RECEIPT_ID)

    assert client._receipt["ocr_status"] == "failed"
    assert client._receipt["ocr_error"] == _SAFE_ERROR_MESSAGE
    assert "internal detail" not in client._receipt["ocr_error"]


async def test_process_receipt_ocr_fails_gracefully_when_unconfigured(monkeypatch):
    client = _FakeAsyncClient(make_receipt())

    async def fake_get_service_client():
        return client

    monkeypatch.setattr(pipeline_module, "get_service_client", fake_get_service_client)
    monkeypatch.setattr(pipeline_module, "get_ocr_provider", lambda: None)

    await process_receipt_ocr(RECEIPT_ID)

    assert client._receipt["ocr_status"] == "failed"
    assert client._receipt["ocr_error"] == _SAFE_ERROR_MESSAGE
