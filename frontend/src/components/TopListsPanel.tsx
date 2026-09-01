import { Receipt as ReceiptIcon, ShoppingBag, Store } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Money } from './Money'
import { EmptyState } from './EmptyState'
import { formatDateNo } from '../lib/format'
import type { components } from '../lib/api/schema'

type TopItem = components['schemas']['TopItem']
type TopMerchant = components['schemas']['TopMerchant']
type TopReceipt = components['schemas']['TopReceipt']

function RankedList<T>({
  title,
  rows,
  emptyIcon,
  renderLabel,
  renderAmount,
}: {
  title: string
  rows: T[]
  emptyIcon: LucideIcon
  renderLabel: (row: T) => string
  renderAmount: (row: T) => string
}) {
  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <h3 className="mb-2 text-sm font-medium text-muted">{title}</h3>
      {rows.length === 0 ? (
        <EmptyState icon={emptyIcon} title="Nothing here yet." compact />
      ) : (
        <ul className="flex flex-col divide-y divide-border">
          {rows.map((row, i) => (
            <li key={i} className="flex items-center justify-between py-2 text-sm">
              <span className="truncate pr-3">{renderLabel(row)}</span>
              <Money amount={renderAmount(row)} className="shrink-0" />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function TopListsPanel({
  items,
  merchants,
  receipts,
}: {
  items: TopItem[]
  merchants: TopMerchant[]
  receipts: TopReceipt[]
}) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <RankedList
        title="Top items"
        rows={items}
        emptyIcon={ShoppingBag}
        renderLabel={(i) => `${i.description} (${i.count}×)`}
        renderAmount={(i) => i.total}
      />
      <RankedList
        title="Top merchants"
        rows={merchants}
        emptyIcon={Store}
        renderLabel={(m) => `${m.merchant} (${m.count}×)`}
        renderAmount={(m) => m.total}
      />
      <RankedList
        title="Priciest receipts"
        rows={receipts}
        emptyIcon={ReceiptIcon}
        renderLabel={(r) => `${r.merchant ?? 'Unknown'} · ${formatDateNo(r.receipt_date)}`}
        renderAmount={(r) => r.total_amount}
      />
    </div>
  )
}
