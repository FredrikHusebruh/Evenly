import { useState } from 'react'
import { useParams } from 'react-router'
import { useReceiptPolling } from '../hooks/useReceiptPolling'
import { useGroupDetail } from '../hooks/useGroupDetail'
import { useSplit } from '../hooks/useSplit'
import { useSession } from '../auth/useSession'
import * as lineItemsApi from '../lib/api/lineItems'
import { ReceiptHeaderFields } from '../components/ReceiptHeaderFields'
import { LineItemRow } from '../components/LineItemRow'
import { MismatchBanner } from '../components/MismatchBanner'
import { SplitSummaryPanel } from '../components/SplitSummaryPanel'
import * as receiptsApi from '../lib/api/receipts'

export function ReceiptReviewPage() {
  const { receiptId, groupId } = useParams<{ receiptId: string; groupId: string }>()
  const { session } = useSession()
  const { receipt, loading, reload } = useReceiptPolling(receiptId!)
  const { group } = useGroupDetail(groupId!)
  const { split, reload: reloadSplit } = useSplit(receiptId!)
  const [adding, setAdding] = useState(false)
  const [retrying, setRetrying] = useState(false)

  async function refreshAfterMutation() {
    await Promise.all([reload(), reloadSplit()])
  }

  async function handleHeaderUpdate(patch: Parameters<typeof receiptsApi.updateReceipt>[1]) {
    await receiptsApi.updateReceipt(receiptId!, patch)
    refreshAfterMutation()
  }

  async function handleItemUpdate(itemId: string, patch: Parameters<typeof lineItemsApi.updateLineItem>[1]) {
    await lineItemsApi.updateLineItem(itemId, patch)
    refreshAfterMutation()
  }

  async function handleItemDelete(itemId: string) {
    await lineItemsApi.deleteLineItem(itemId)
    refreshAfterMutation()
  }

  async function handleRetryOcr() {
    setRetrying(true)
    try {
      await receiptsApi.retryOcr(receiptId!)
      await reload()
    } finally {
      setRetrying(false)
    }
  }

  async function handleAddItem() {
    setAdding(true)
    try {
      await lineItemsApi.createLineItem(receiptId!, {
        description: 'New item',
        quantity: 1,
        unit_price: 0,
        total_price: 0,
      })
      await refreshAfterMutation()
    } finally {
      setAdding(false)
    }
  }

  if (loading || !receipt) return <p className="text-sm text-muted">Loading…</p>

  if (receipt.ocr_status === 'pending' || receipt.ocr_status === 'processing') {
    return (
      <div className="flex flex-col gap-4">
        <div className="h-6 w-40 animate-pulse rounded-sm bg-surface" />
        <div className="h-32 animate-pulse rounded-md bg-surface" />
        <p className="text-sm text-muted">Processing receipt…</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold tracking-tight">Review receipt</h1>

      {receipt.ocr_status === 'failed' && (
        <div className="flex items-center gap-3">
          <p className="text-sm text-owed">{receipt.ocr_error ?? 'Processing failed. Add items manually below.'}</p>
          <button
            type="button"
            onClick={handleRetryOcr}
            disabled={retrying}
            className="text-sm text-accent hover:text-accent-hover disabled:opacity-60"
          >
            {retrying ? 'Retrying…' : 'Retry'}
          </button>
        </div>
      )}

      <ReceiptHeaderFields receipt={receipt} onUpdate={handleHeaderUpdate} />

      {receipt.mismatch && <MismatchBanner />}

      <div className="flex flex-col">
        {receipt.line_items.map((item) => (
          <LineItemRow
            key={item.id}
            item={item}
            members={group?.members ?? []}
            currentUserId={session?.user.id}
            onUpdate={(patch) => handleItemUpdate(item.id, patch)}
            onDelete={() => handleItemDelete(item.id)}
          />
        ))}
        <button
          type="button"
          onClick={handleAddItem}
          disabled={adding}
          className="mt-3 self-start text-sm text-accent hover:text-accent-hover disabled:opacity-60"
        >
          + Add item
        </button>
      </div>

      {split && <SplitSummaryPanel split={split} currentUserId={session?.user.id} />}
    </div>
  )
}
