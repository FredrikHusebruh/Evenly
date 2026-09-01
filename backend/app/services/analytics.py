from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from supabase import AsyncClient

from app.schemas.analytics import (
    CategoryBreakdown,
    GroupAnalyticsOut,
    MemberHistoryPoint,
    SpendingTrendPoint,
    TopItem,
    TopMerchant,
    TopReceipt,
)
from app.schemas.line_item import LineItemOut
from app.services.split import compute_split

TOP_LIST_LIMIT = 10
TOP_RECEIPTS_LIMIT = 5


def _period(receipt: dict) -> str:
    return (receipt["receipt_date"] or receipt["created_at"])[:7]


async def get_group_analytics(db: AsyncClient, group_id: UUID, user_id: UUID) -> GroupAnalyticsOut:
    receipts_res = await db.table("receipts").select("*").eq("group_id", str(group_id)).execute()
    receipts = receipts_res.data

    categories_res = await db.table("categories").select("id, name").eq("group_id", str(group_id)).execute()
    category_names = {c["id"]: c["name"] for c in categories_res.data}

    members_res = await db.table("group_members").select("user_id").eq("group_id", str(group_id)).execute()
    member_ids = [UUID(m["user_id"]) for m in members_res.data]

    receipt_ids = [r["id"] for r in receipts]
    line_items_by_receipt: dict[str, list[LineItemOut]] = defaultdict(list)
    if receipt_ids:
        items_res = await db.table("line_items").select("*").in_("receipt_id", receipt_ids).execute()
        for item in items_res.data:
            line_items_by_receipt[item["receipt_id"]].append(LineItemOut.model_validate(item))

    total_spent = Decimal(0)
    category_totals: dict[str | None, Decimal] = defaultdict(Decimal)
    category_counts: dict[str | None, int] = defaultdict(int)
    trend_totals: dict[str, Decimal] = defaultdict(Decimal)
    merchant_totals: dict[str, Decimal] = defaultdict(Decimal)
    merchant_counts: dict[str, int] = defaultdict(int)
    item_totals: dict[str, Decimal] = defaultdict(Decimal)
    item_counts: dict[str, int] = defaultdict(int)
    paid_by_period: dict[str, Decimal] = defaultdict(Decimal)
    owed_by_period: dict[str, Decimal] = defaultdict(Decimal)

    for receipt in receipts:
        amount = Decimal(str(receipt["total_amount"])) if receipt["total_amount"] is not None else Decimal(0)
        total_spent += amount

        category_id = receipt["category_id"]
        category_totals[category_id] += amount
        category_counts[category_id] += 1

        period = _period(receipt)
        trend_totals[period] += amount

        merchant = receipt["merchant"]
        if merchant:
            merchant_totals[merchant] += amount
            merchant_counts[merchant] += 1

        items = line_items_by_receipt.get(receipt["id"], [])
        for item in items:
            # Naive text grouping — "Melk 1L" and "Melk" won't merge. Not worth a
            # fuzzy-match system for a v1 top-items list.
            key = item.description.strip().lower()
            item_totals[key] += item.total_price
            item_counts[key] += 1

        receipt_total = Decimal(str(receipt["total_amount"])) if receipt["total_amount"] is not None else None
        split = compute_split(items, member_ids, receipt_total)
        my_split = next((m for m in split.member_splits if m.user_id == user_id), None)
        if my_split:
            owed_by_period[period] += my_split.owed_total
        if UUID(receipt["uploaded_by"]) == user_id:
            paid_by_period[period] += amount

    category_breakdown = sorted(
        (
            CategoryBreakdown(
                category_id=UUID(cid) if cid else None,
                category_name=category_names.get(cid, "Uncategorized") if cid else "Uncategorized",
                total=total,
                receipt_count=category_counts[cid],
            )
            for cid, total in category_totals.items()
        ),
        key=lambda c: c.total,
        reverse=True,
    )

    spending_trend = [SpendingTrendPoint(period=p, total=trend_totals[p]) for p in sorted(trend_totals)]

    all_periods = sorted(set(paid_by_period) | set(owed_by_period))
    member_history = [
        MemberHistoryPoint(period=p, paid=paid_by_period.get(p, Decimal(0)), owed=owed_by_period.get(p, Decimal(0)))
        for p in all_periods
    ]

    top_items = sorted(
        (TopItem(description=desc, count=item_counts[desc], total=total) for desc, total in item_totals.items()),
        key=lambda i: i.total,
        reverse=True,
    )[:TOP_LIST_LIMIT]

    top_merchants = sorted(
        (TopMerchant(merchant=m, count=merchant_counts[m], total=total) for m, total in merchant_totals.items()),
        key=lambda m: m.total,
        reverse=True,
    )[:TOP_LIST_LIMIT]

    top_receipts = sorted(
        receipts,
        key=lambda r: Decimal(str(r["total_amount"])) if r["total_amount"] is not None else Decimal(0),
        reverse=True,
    )[:TOP_RECEIPTS_LIMIT]
    top_receipts_out = [
        TopReceipt(
            id=UUID(r["id"]),
            merchant=r["merchant"],
            receipt_date=r["receipt_date"],
            total_amount=Decimal(str(r["total_amount"])) if r["total_amount"] is not None else Decimal(0),
        )
        for r in top_receipts
    ]

    return GroupAnalyticsOut(
        total_spent=total_spent,
        receipt_count=len(receipts),
        category_breakdown=category_breakdown,
        spending_trend=spending_trend,
        member_history=member_history,
        top_items=top_items,
        top_merchants=top_merchants,
        top_receipts=top_receipts_out,
    )
