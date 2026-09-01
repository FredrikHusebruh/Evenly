import { useNavigate } from 'react-router'
import { Receipt as ReceiptIcon } from 'lucide-react'
import { formatDateNo, formatNok } from '../lib/format'
import { Money } from './Money'
import { Skeleton } from './Skeleton'
import { EmptyState } from './EmptyState'
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
}: {
  groupId: string
  receipts: Receipt[]
  loading?: boolean
}) {
  const navigate = useNavigate()

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

  return (
    <>
      <ul className="flex flex-col divide-y divide-border border-y border-border sm:hidden">
        {receipts.map((receipt) => (
          <li key={receipt.id}>
            <button
              type="button"
              onClick={() => navigate(`/groups/${groupId}/receipts/${receipt.id}`)}
              className="flex w-full items-center justify-between px-1 py-3 text-left"
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
