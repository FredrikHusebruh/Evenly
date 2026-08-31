from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.schemas.line_item import LineItemOut
from app.services.split import compute_split, simplify_debts

RECEIPT_ID = uuid4()


def make_item(
    total_price: str,
    status: str = "shared",
    assigned_to: UUID | None = None,
    unit_price: str | None = None,
) -> LineItemOut:
    return LineItemOut(
        id=uuid4(),
        receipt_id=RECEIPT_ID,
        description="Item",
        quantity=Decimal(1),
        unit_price=Decimal(unit_price or total_price),
        total_price=Decimal(total_price),
        created_at=datetime.now(UTC),
        status=status,
        assigned_to=assigned_to,
    )


def members(n: int) -> list[UUID]:
    # Fixed, deterministically sorted-by-str UUIDs so expected per-member
    # remainder assignment is stable across test runs.
    return sorted((uuid4() for _ in range(n)), key=str)


def test_equal_split_divides_evenly_across_two_members():
    m1, m2 = members(2)
    items = [make_item("100.00")]
    result = compute_split(items, [m1, m2], receipt_total=Decimal("100.00"))

    assert result.shared_total == Decimal("100.00")
    shares = {ms.user_id: ms.owed_total for ms in result.member_splits}
    assert shares[m1] == Decimal("50.00")
    assert shares[m2] == Decimal("50.00")
    assert sum(shares.values()) == Decimal("100.00")
    assert result.mismatch is False


def test_equal_split_reconciles_exact_ore_across_three_members():
    group = members(3)
    items = [make_item("100.00")]
    result = compute_split(items, group, receipt_total=Decimal("100.00"))

    shares = {ms.user_id: ms.owed_total for ms in result.member_splits}
    # 100.00 / 3 = 33.33 remainder 1 ore -> one member gets 33.34
    assert sum(shares.values()) == Decimal("100.00")
    assert sorted(shares.values()) == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]


def test_equal_split_reconciles_exact_ore_across_four_members():
    group = members(4)
    items = [make_item("10.00")]
    result = compute_split(items, group, receipt_total=Decimal("10.00"))

    shares = [ms.owed_total for ms in result.member_splits]
    assert sum(shares) == Decimal("10.00")
    assert sorted(shares) == [Decimal("2.50")] * 4


def test_equal_split_reconciles_exact_ore_across_five_members():
    group = members(5)
    items = [make_item("100.01")]
    result = compute_split(items, group, receipt_total=Decimal("100.01"))

    shares = [ms.owed_total for ms in result.member_splits]
    assert sum(shares) == Decimal("100.01")
    # 100.01 / 5 = 20.00 remainder 1 ore
    assert sorted(shares) == [Decimal("20.00")] * 4 + [Decimal("20.01")]


def test_personal_items_excluded_from_shared_pool():
    m1, m2 = members(2)
    items = [
        make_item("100.00", status="shared"),
        make_item("30.00", status="personal", assigned_to=m1),
    ]
    result = compute_split(items, [m1, m2], receipt_total=Decimal("130.00"))

    assert result.shared_total == Decimal("100.00")
    shares = {ms.user_id: ms for ms in result.member_splits}
    assert shares[m1].personal_total == Decimal("30.00")
    assert shares[m1].shared_share == Decimal("50.00")
    assert shares[m1].owed_total == Decimal("80.00")
    assert shares[m2].personal_total == Decimal(0)
    assert shares[m2].owed_total == Decimal("50.00")


def test_excluded_items_excluded_from_everything():
    m1, m2 = members(2)
    items = [
        make_item("100.00", status="shared"),
        make_item("999.99", status="excluded"),
    ]
    # receipt_total matches the sum of *all* parsed items (shared + excluded)
    # so this test isolates "excluded items don't affect the split" from the
    # mismatch check, which is covered separately below.
    result = compute_split(items, [m1, m2], receipt_total=Decimal("1099.99"))

    assert result.shared_total == Decimal("100.00")
    assert result.excluded_total == Decimal("999.99")
    assert sum(ms.owed_total for ms in result.member_splits) == Decimal("100.00")
    assert result.mismatch is False


def test_mismatch_detects_sum_of_all_items_vs_receipt_total():
    m1, m2 = members(2)
    items = [make_item("50.00", status="shared"), make_item("40.00", status="excluded")]
    # items_total (all statuses) = 90.00, receipt says 100.00 -> mismatch
    result = compute_split(items, [m1, m2], receipt_total=Decimal("100.00"))
    assert result.mismatch is True


def test_mismatch_within_tolerance_is_not_flagged():
    m1, m2 = members(2)
    items = [make_item("50.01", status="shared")]
    result = compute_split(items, [m1, m2], receipt_total=Decimal("50.01"))
    assert result.mismatch is False


def test_mismatch_none_receipt_total_is_never_flagged():
    m1, m2 = members(2)
    items = [make_item("50.00", status="shared")]
    result = compute_split(items, [m1, m2], receipt_total=None)
    assert result.mismatch is False


def test_empty_receipt_no_items():
    m1, m2 = members(2)
    result = compute_split([], [m1, m2], receipt_total=None)
    assert result.shared_total == Decimal(0)
    assert all(ms.owed_total == Decimal(0) for ms in result.member_splits)


def test_single_member_group_gets_entire_shared_total():
    (m1,) = members(1)
    items = [make_item("77.77")]
    result = compute_split(items, [m1], receipt_total=Decimal("77.77"))
    assert result.member_splits[0].owed_total == Decimal("77.77")


def test_simplify_debts_nets_to_zero_and_minimizes_transactions():
    a, b, c = members(3)
    # a is owed 100 total, b and c each owe 50
    net_balances = {a: Decimal("100.00"), b: Decimal("-50.00"), c: Decimal("-50.00")}
    settlements = simplify_debts(net_balances)

    assert sum(s.amount for s in settlements) == Decimal("100.00")
    assert len(settlements) == 2
    paid_to_a = sum(s.amount for s in settlements if s.to_user == a)
    assert paid_to_a == Decimal("100.00")
    for s in settlements:
        assert s.to_user == a
        assert s.from_user in (b, c)


def test_simplify_debts_multi_receipt_multi_payer_nets_correctly():
    a, b, c = members(3)
    # Two receipts with different payers, aggregated net balances.
    # Receipt 1: a pays 90, split evenly 3 ways (30 each) -> a is owed 60 (b:30, c:30)
    #   effect: a +60, b -30, c -30
    # Receipt 2: b pays 60, split evenly 3 ways (20 each) -> b is owed 40 (a:20, c:20)
    #   effect: a -20, b +40, c -20
    # Net: a = +60-20 = +40, b = -30+40 = +10, c = -30-20 = -50
    net_balances = {a: Decimal("40.00"), b: Decimal("10.00"), c: Decimal("-50.00")}
    assert sum(net_balances.values()) == Decimal(0)

    settlements = simplify_debts(net_balances)
    assert sum(s.amount for s in settlements) == Decimal("50.00")

    resulting_balances = dict.fromkeys(net_balances, Decimal(0))
    for s in settlements:
        resulting_balances[s.from_user] -= s.amount
        resulting_balances[s.to_user] += s.amount
    for uid, balance in net_balances.items():
        assert resulting_balances[uid] == balance


def test_simplify_debts_empty_when_all_settled():
    a, b = members(2)
    assert simplify_debts({a: Decimal(0), b: Decimal(0)}) == []
