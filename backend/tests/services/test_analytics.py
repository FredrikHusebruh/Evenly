from decimal import Decimal
from uuid import UUID

from app.services.analytics import get_group_analytics

GROUP_ID = UUID("11111111-1111-1111-1111-111111111111")
USER_ID = UUID("22222222-2222-2222-2222-222222222222")
OTHER_USER_ID = UUID("33333333-3333-3333-3333-333333333333")
CATEGORY_ID = "44444444-4444-4444-4444-444444444444"


def _uuid(n: int) -> str:
    return f"00000000-0000-0000-0000-{n:012d}"


class _FakeQueryBuilder:
    def __init__(self, client, table_name):
        self._client = client
        self._table_name = table_name

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def in_(self, *_args, **_kwargs):
        return self

    async def execute(self):
        return type("R", (), {"data": self._client.data[self._table_name]})()


class _FakeAsyncClient:
    """Ignores filter args entirely — each test's canned data already only
    contains rows for the group/receipts under test, matching the fake-client
    style used elsewhere in this suite (test_line_items.py, test_receipts.py)."""

    def __init__(self, *, receipts, categories=(), members=(USER_ID, OTHER_USER_ID), line_items=()):
        self.data = {
            "receipts": list(receipts),
            "categories": list(categories),
            "group_members": [{"user_id": str(uid)} for uid in members],
            "line_items": list(line_items),
        }

    def table(self, name):
        return _FakeQueryBuilder(self, name)


def _receipt(n: int, **overrides):
    base = {
        "id": _uuid(n),
        "uploaded_by": str(USER_ID),
        "category_id": None,
        "merchant": "Kiwi",
        "total_amount": "100.00",
        "receipt_date": "2026-01-15",
        "created_at": "2026-01-15T10:00:00Z",
    }
    base.update(overrides)
    return base


def _line_item(n: int, receipt_n: int, **overrides):
    base = {
        "id": _uuid(1000 + n),
        "receipt_id": _uuid(receipt_n),
        "description": "Item",
        "quantity": "1",
        "unit_price": "10.00",
        "total_price": "10.00",
        "created_at": "2026-01-15T10:00:00Z",
        "status": "shared",
        "assigned_to": None,
    }
    base.update(overrides)
    return base


async def test_category_breakdown_groups_uncategorized_receipt():
    client = _FakeAsyncClient(
        receipts=[
            _receipt(1, category_id=CATEGORY_ID, total_amount="50.00"),
            _receipt(2, category_id=None, total_amount="30.00"),
        ],
        categories=[{"id": CATEGORY_ID, "name": "Groceries"}],
    )

    result = await get_group_analytics(client, GROUP_ID, USER_ID)

    by_category = {c.category_name: c for c in result.category_breakdown}
    assert by_category["Groceries"].total == Decimal("50.00")
    assert by_category["Groceries"].receipt_count == 1
    assert by_category["Uncategorized"].total == Decimal("30.00")
    assert result.total_spent == Decimal("80.00")


async def test_spending_trend_buckets_by_month():
    client = _FakeAsyncClient(
        receipts=[
            _receipt(1, receipt_date="2026-01-05", total_amount="10.00"),
            _receipt(2, receipt_date="2026-01-20", total_amount="15.00"),
            _receipt(3, receipt_date="2026-02-01", total_amount="20.00"),
        ]
    )

    result = await get_group_analytics(client, GROUP_ID, USER_ID)

    assert [p.period for p in result.spending_trend] == ["2026-01", "2026-02"]
    assert result.spending_trend[0].total == Decimal("25.00")
    assert result.spending_trend[1].total == Decimal("20.00")


async def test_member_history_splits_paid_and_owed_by_period():
    client = _FakeAsyncClient(
        receipts=[
            _receipt(1, uploaded_by=str(USER_ID), receipt_date="2026-01-10", total_amount="100.00"),
            _receipt(2, uploaded_by=str(OTHER_USER_ID), receipt_date="2026-02-10", total_amount="50.00"),
        ],
        line_items=[
            _line_item(1, 1, status="shared", total_price="100.00"),
            _line_item(2, 2, status="shared", total_price="50.00"),
        ],
    )

    result = await get_group_analytics(client, GROUP_ID, USER_ID)

    by_period = {p.period: p for p in result.member_history}
    assert by_period["2026-01"].paid == Decimal("100.00")
    assert by_period["2026-01"].owed == Decimal("50.00")  # my even split of the shared item
    assert by_period["2026-02"].paid == Decimal(0)  # I didn't upload r2
    assert by_period["2026-02"].owed == Decimal("25.00")  # still owe my share of it


async def test_top_items_merges_case_and_caps_at_ten():
    items = [_line_item(n, 1, description="Milk", total_price="5.00") for n in range(5)]
    items += [_line_item(5 + n, 1, description="milk", total_price="5.00") for n in range(5)]
    items += [
        _line_item(10 + n, 1, description=f"Unique item {n}", total_price=f"{n + 1}.00") for n in range(12)
    ]

    client = _FakeAsyncClient(receipts=[_receipt(1)], line_items=items)

    result = await get_group_analytics(client, GROUP_ID, USER_ID)

    assert len(result.top_items) == 10
    top = result.top_items[0]
    assert top.description == "milk"
    assert top.count == 10
    assert top.total == Decimal("50.00")


async def test_top_receipts_sorts_descending_and_caps_at_five():
    receipts = [_receipt(n, total_amount=f"{n * 10}.00") for n in range(8)]

    client = _FakeAsyncClient(receipts=receipts)

    result = await get_group_analytics(client, GROUP_ID, USER_ID)

    assert len(result.top_receipts) == 5
    assert [r.total_amount for r in result.top_receipts] == [
        Decimal("70.00"),
        Decimal("60.00"),
        Decimal("50.00"),
        Decimal("40.00"),
        Decimal("30.00"),
    ]
