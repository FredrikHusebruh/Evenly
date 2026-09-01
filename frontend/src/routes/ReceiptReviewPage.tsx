import { useState } from 'react'
import { useParams } from 'react-router'
import { Plus } from 'lucide-react'
import { useReceiptPolling } from '../hooks/useReceiptPolling'
import { useGroupDetail } from '../hooks/useGroupDetail'
import { useSplit } from '../hooks/useSplit'
import { useOptimisticLineItems } from '../hooks/useOptimisticLineItems'
import { useSession } from '../auth/useSession'
import { useToast } from '../toast/useToast'
import * as lineItemsApi from '../lib/api/lineItems'
import type { LineItemPatch } from '../lib/api/lineItems'
import { ReceiptHeaderFields } from '../components/ReceiptHeaderFields'
import { LineItemRow } from '../components/LineItemRow'
import { MismatchBanner } from '../components/MismatchBanner'
import { SplitSummaryPanel } from '../components/SplitSummaryPanel'
import { Skeleton } from '../components/Skeleton'
import * as receiptsApi from '../lib/api/receipts'

export function ReceiptReviewPage() {
  const { receiptId, groupId } = useParams<{ receiptId: string; groupId: string }>()
  const { session } = useSession()
  const { showToast } = useToast()
  const { receipt, loading, reload } = useReceiptPolling(receiptId!)
  const { group } = useGroupDetail(groupId!)
  const isOcrDone = receipt?.ocr_status === 'succeeded' || receipt?.ocr_status === 'failed'
  const { split, loading: splitLoading, reload: reloadSplit } = useSplit(receiptId!, isOcrDone)
  const { items, updateItem, deleteItem, error: itemsError } = useOptimisticLineItems(receipt?.line_items ?? [])
  const [adding, setAdding] = useState(false)
  const [retrying, setRetrying] = useState(false)

  async function refreshAfterMutation() {
    await Promise.all([reload(), reloadSplit()])
  }

  async function handleHeaderUpdate(patch: Parameters<typeof receiptsApi.updateReceipt>[1]) {
    await receiptsApi.updateReceipt(receiptId!, patch)
    refreshAfterMutation()
  }

  async function handleItemUpdate(itemId: string, patch: LineItemPatch) {
    const ok = await updateItem(itemId, patch)
    if (ok) showToast('Item updated')
    refreshAfterMutation()
  }

  async function handleItemDelete(itemId: string) {
    const ok = await deleteItem(itemId)
    if (ok) showToast('Item removed')
    refreshAfterMutation()
  }

  async function handleRetryOcr() {
    setRetrying(true)
    try {
      await receiptsApi.retryOcr(receiptId!)
      await reload()
      showToast('OCR retry started')
    } catch {
      showToast('Failed to retry OCR', 'error')
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

  if (loading || !receipt) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-32 w-full rounded-md" />
      </div>
    )
  }

  if (receipt.ocr_status === 'pending' || receipt.ocr_status === 'processing') {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-32 w-full rounded-md" />
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
      {itemsError && <p className="text-sm text-owed">{itemsError}</p>}

      <div className="bg-surface shadow-sm">
        <div className="receipt-torn-top" />
        <div className="flex flex-col px-5 py-4">
          <div className="flex flex-col">
            {items.map((item) => (
              <LineItemRow
                key={item.id}
                item={item}
                members={group?.members ?? []}
                currentUserId={session?.user.id}
                onUpdate={(patch) => handleItemUpdate(item.id, patch)}
                onDelete={() => handleItemDelete(item.id)}
              />
            ))}
          </div>
          <button
            type="button"
            onClick={handleAddItem}
            disabled={adding}
            className="mt-3 flex items-center gap-1 self-start font-mono text-sm text-accent hover:text-accent-hover disabled:opacity-60"
          >
            <Plus className="h-4 w-4" strokeWidth={1.75} /> Add item
          </button>

          {split && (
            <SplitSummaryPanel
              split={split}
              members={group?.members ?? []}
              currentUserId={session?.user.id}
              loading={splitLoading}
            />
          )}
        </div>
        <div className="receipt-torn-bottom" />
      </div>
    </div>
  )
}
