"""Split-calculation engine. Pure functions, no I/O — all money as Decimal.

Split state (shared/personal/excluded) lives directly on each line item.
Equal-split "shared" amounts are computed here from the group's *current*
members, never persisted per-item, so a membership change is reflected
immediately on the next calculation rather than needing a backfill.
"""

from decimal import Decimal
from uuid import UUID

from supabase import AsyncClient

from app.clients.supabase import unwrap_maybe_single
from app.errors import NotFoundError
from app.schemas.line_item import LineItemOut
from app.schemas.split import MemberSplit, Settlement, SettleUpOut, SplitResult

MISMATCH_TOLERANCE = Decimal("0.01")


def compute_mismatch(items_total: Decimal, receipt_total: Decimal | None) -> bool:
    if receipt_total is None:
        return False
    return abs(items_total - receipt_total) > MISMATCH_TOLERANCE


def _split_equally(total: Decimal, member_ids: list[UUID]) -> dict[UUID, Decimal]:
    """Largest-remainder split in whole øre, so shares sum exactly to total."""
    if not member_ids:
        return {}
    total_ore = int(total * 100)
    base_ore, remainder = divmod(total_ore, len(member_ids))
    ordered = sorted(member_ids, key=str)
    shares_ore = {uid: base_ore for uid in ordered}
    for uid in ordered[:remainder]:
        shares_ore[uid] += 1
    return {uid: Decimal(shares_ore[uid]) / 100 for uid in member_ids}


def compute_split(
    line_items: list[LineItemOut],
    member_ids: list[UUID],
    receipt_total: Decimal | None,
) -> SplitResult:
    shared_items = [li for li in line_items if li.status == "shared"]
    personal_items = [li for li in line_items if li.status == "personal"]
    excluded_items = [li for li in line_items if li.status == "excluded"]

    shared_total = sum((li.total_price for li in shared_items), Decimal(0))
    excluded_total = sum((li.total_price for li in excluded_items), Decimal(0))

    personal_totals: dict[UUID, Decimal] = {uid: Decimal(0) for uid in member_ids}
    for li in personal_items:
        if li.assigned_to in personal_totals:
            personal_totals[li.assigned_to] += li.total_price

    shared_shares = _split_equally(shared_total, member_ids)

    member_splits = [
        MemberSplit(
            user_id=uid,
            personal_total=personal_totals.get(uid, Decimal(0)),
            shared_share=shared_shares.get(uid, Decimal(0)),
            owed_total=personal_totals.get(uid, Decimal(0)) + shared_shares.get(uid, Decimal(0)),
        )
        for uid in member_ids
    ]

    items_total = sum((li.total_price for li in line_items), Decimal(0))

    return SplitResult(
        shared_total=shared_total,
        excluded_total=excluded_total,
        member_splits=member_splits,
        mismatch=compute_mismatch(items_total, receipt_total),
    )


def simplify_debts(net_balances: dict[UUID, Decimal]) -> list[Settlement]:
    """Greedy largest-creditor/largest-debtor matching.

    net_balances[user] > 0 means the user is owed money overall;
    < 0 means the user owes money overall. Must sum to zero.
    """
    creditors = sorted(
        ([uid, bal] for uid, bal in net_balances.items() if bal > 0),
        key=lambda pair: (-pair[1], str(pair[0])),
    )
    debtors = sorted(
        ([uid, -bal] for uid, bal in net_balances.items() if bal < 0),
        key=lambda pair: (-pair[1], str(pair[0])),
    )

    settlements: list[Settlement] = []
    i = j = 0
    while i < len(creditors) and j < len(debtors):
        creditor_id, credit = creditors[i]
        debtor_id, debt = debtors[j]
        amount = min(credit, debt)
        if amount > 0:
            settlements.append(Settlement(from_user=debtor_id, to_user=creditor_id, amount=amount))
        creditors[i][1] -= amount
        debtors[j][1] -= amount
        if creditors[i][1] == 0:
            i += 1
        if debtors[j][1] == 0:
            j += 1
    return settlements


async def get_receipt_split(db: AsyncClient, receipt_id: UUID) -> SplitResult:
    receipt_res = (
        await db.table("receipts").select("group_id, total_amount").eq("id", str(receipt_id)).maybe_single().execute()
    )
    receipt = unwrap_maybe_single(receipt_res)
    if not receipt:
        raise NotFoundError("Receipt not found")

    members_res = await db.table("group_members").select("user_id").eq("group_id", receipt["group_id"]).execute()
    member_ids = [UUID(m["user_id"]) for m in members_res.data]

    items_res = (
        await db.table("line_items").select("*").eq("receipt_id", str(receipt_id)).order("created_at").execute()
    )
    line_items = [LineItemOut.model_validate(i) for i in items_res.data]

    total_amount = receipt.get("total_amount")
    receipt_total = Decimal(str(total_amount)) if total_amount is not None else None

    return compute_split(line_items, member_ids, receipt_total)


async def get_settle_up(db: AsyncClient, group_id: UUID) -> SettleUpOut:
    members_res = await db.table("group_members").select("user_id").eq("group_id", str(group_id)).execute()
    member_ids = [UUID(m["user_id"]) for m in members_res.data]
    net_balances: dict[UUID, Decimal] = {uid: Decimal(0) for uid in member_ids}

    receipts_res = (
        await db.table("receipts").select("id, uploaded_by, total_amount").eq("group_id", str(group_id)).execute()
    )

    for receipt in receipts_res.data:
        payer_id = UUID(receipt["uploaded_by"])
        items_res = await db.table("line_items").select("*").eq("receipt_id", receipt["id"]).execute()
        line_items = [LineItemOut.model_validate(i) for i in items_res.data]
        total_amount = receipt.get("total_amount")
        receipt_total = Decimal(str(total_amount)) if total_amount is not None else None

        split = compute_split(line_items, member_ids, receipt_total)
        for member_split in split.member_splits:
            if member_split.user_id == payer_id:
                continue
            net_balances[payer_id] += member_split.owed_total
            net_balances[member_split.user_id] -= member_split.owed_total

    return SettleUpOut(settlements=simplify_debts(net_balances))
