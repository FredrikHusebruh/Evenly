import { useNavigate } from 'react-router'
import { formatDateNo } from '../lib/format'
import { Money } from './Money'
import type { components } from '../lib/api/schema'

type Receipt = components['schemas']['ReceiptOut']

export function ReceiptHistoryTable({ groupId, receipts }: { groupId: string; receipts: Receipt[] }) {
  const navigate = useNavigate()

  if (receipts.length === 0) {
    return <p className="text-sm text-muted">No receipts yet.</p>
  }

  return (
    <table className="w-full border-collapse text-sm">
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
              {receipt.total_amount != null ? <Money amount={receipt.total_amount} /> : '—'}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
