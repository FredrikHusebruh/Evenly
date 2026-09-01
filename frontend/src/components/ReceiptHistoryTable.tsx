import { useNavigate } from 'react-router'
import { CheckCircle2, Circle, Receipt as ReceiptIcon } from 'lucide-react'
import { formatDateNo, formatNok } from '../lib/format'
import { Money } from './Money'
import { Skeleton } from './Skeleton'
import { EmptyState } from './EmptyState'
import { useToast } from '../toast/useToast'
import * as receiptsApi from '../lib/api/receipts'
import type { components } from '../lib/api/schema'

type Receipt = components['schemas']['ReceiptOut']

function SharedTotal({ receipt }: { receipt: Receipt }) {
  if (receipt.shared_total == null) return null
  return <span className="text-xs text-muted">({formatNok(receipt.shared_total)})</span>
}

export function ReceiptHistoryTable({
  groupId,
  receipts,
  loading = false,
  onChange,
}: {
  groupId: string
  receipts: Receipt[]
  loading?: boolean
  onChange: () => void
}) {
  const navigate = useNavigate()
  const { showToast } = useToast()

  async function handleToggleDone(receipt: Receipt) {
    try {
      await receiptsApi.updateReceipt(receipt.id, { is_done: !receipt.is_done })
      showToast(receipt.is_done ? 'Marked as not done' : 'Marked as done')
      onChange()
    } catch {
      showToast('Failed to update', 'error')
    }
  }

  function DoneToggle({ receipt }: { receipt: Receipt }) {
    return (
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation()
          handleToggleDone(receipt)
        }}
        aria-label={receipt.is_done ? 'Mark as not done' : 'Mark as done'}
        className="shrink-0 p-1 text-muted hover:text-accent"
      >
        {receipt.is_done ? (
          <CheckCircle2 className="h-5 w-5 text-accent" strokeWidth={2} />
        ) : (
          <Circle className="h-5 w-5" strokeWidth={1.75} />
        )}
      </button>
    )
  }

  if (loading) {
    return (
      <div className="flex flex-col divide-y divide-border border-y border-border">
        {[0, 1, 2].map((i) => (
          <div key={i} className="flex items-center justify-between px-1 py-3">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-16" />
          </div>
        ))}
      </div>
    )
  }

  if (receipts.length === 0) {
    return <EmptyState icon={ReceiptIcon} title="No receipts yet." />
  }

  const notDone = receipts.filter((r) => !r.is_done)
  const outstandingTotal = notDone.reduce((sum, r) => sum + Number(r.total_amount ?? 0), 0)
  const outstandingSubtotal = notDone.reduce((sum, r) => sum + Number(r.shared_total ?? 0), 0)

  return (
    <>
      <div className="mb-3 flex items-center justify-between rounded-md border border-border bg-surface px-3 py-2.5">
        <span className="text-sm text-muted">Outstanding (not done)</span>
        <span className="flex items-baseline gap-1">
          <Money amount={outstandingTotal} className="font-semibold" />
          <span className="text-xs text-muted">({formatNok(outstandingSubtotal)})</span>
        </span>
      </div>

      <ul className="flex flex-col divide-y divide-border border-y border-border sm:hidden">
        {receipts.map((receipt) => (
          <li key={receipt.id} className="flex items-center gap-2 px-1 py-2">
            <DoneToggle receipt={receipt} />
            <button
              type="button"
              onClick={() => navigate(`/groups/${groupId}/receipts/${receipt.id}`)}
              className="flex flex-1 items-center justify-between py-1 text-left"
            >
              <span className="flex flex-col">
                <span className="text-sm">{receipt.merchant ?? '—'}</span>
                <span className="text-xs text-muted">{formatDateNo(receipt.receipt_date)}</span>
              </span>
              {receipt.total_amount != null ? (
                <span className="flex items-baseline gap-1">
                  <Money amount={receipt.total_amount} />
                  <SharedTotal receipt={receipt} />
                </span>
              ) : (
                <span className="text-muted">—</span>
              )}
            </button>
          </li>
        ))}
      </ul>

      <table className="hidden w-full border-collapse text-sm sm:table">
        <thead>
          <tr className="border-b border-border text-left text-muted">
            <th className="w-8 py-2" />
            <th className="py-2 font-medium">Store</th>
            <th className="py-2 font-medium">Date</th>
            <th className="py-2 text-right font-medium">Total</th>
          </tr>
        </thead>
        <tbody>
          {receipts.map((receipt) => (
            <tr
              key={receipt.id}
              onClick={() => navigate(`/groups/${groupId}/receipts/${receipt.id}`)}
              className="cursor-pointer border-b border-border last:border-0 hover:bg-surface"
            >
              <td className="py-2.5">
                <DoneToggle receipt={receipt} />
              </td>
              <td className="py-2.5">{receipt.merchant ?? '—'}</td>
              <td className="py-2.5 text-muted">{formatDateNo(receipt.receipt_date)}</td>
              <td className="py-2.5 text-right">
                {receipt.total_amount != null ? (
                  <span className="inline-flex items-baseline gap-1">
                    <Money amount={receipt.total_amount} />
                    <SharedTotal receipt={receipt} />
                  </span>
                ) : (
                  '—'
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}
