import { useState } from 'react'
import type { components } from '../lib/api/schema'

type ReceiptDetail = components['schemas']['ReceiptDetail']

export function ReceiptHeaderFields({
  receipt,
  onUpdate,
}: {
  receipt: ReceiptDetail
  onUpdate: (patch: { merchant?: string; total_amount?: number; receipt_date?: string }) => void
}) {
  const [merchant, setMerchant] = useState(receipt.merchant ?? '')
  const [date, setDate] = useState(receipt.receipt_date ?? '')
  const [total, setTotal] = useState(receipt.total_amount ?? '')

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <label className="flex flex-col gap-1">
        <span className="text-xs text-muted">Store</span>
        <input
          value={merchant}
          onChange={(e) => setMerchant(e.target.value)}
          onBlur={() => merchant !== (receipt.merchant ?? '') && onUpdate({ merchant })}
          className="rounded-sm border border-border bg-surface px-2 py-1.5 text-sm outline-none focus:border-accent"
        />
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-xs text-muted">Date</span>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          onBlur={() => date !== (receipt.receipt_date ?? '') && onUpdate({ receipt_date: date })}
          className="rounded-sm border border-border bg-surface px-2 py-1.5 text-sm outline-none focus:border-accent"
        />
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-xs text-muted">Total (kr)</span>
        <input
          value={total}
          onChange={(e) => setTotal(e.target.value)}
          onBlur={() => total !== (receipt.total_amount ?? '') && onUpdate({ total_amount: Number(total) })}
          className="rounded-sm border border-border bg-surface px-2 py-1.5 text-right text-sm tabular-nums outline-none focus:border-accent"
        />
      </label>
    </div>
  )
}
