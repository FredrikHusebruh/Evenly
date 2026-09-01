import { useEffect, useRef, useState } from 'react'
import * as lineItemsApi from '../lib/api/lineItems'
import type { LineItemPatch } from '../lib/api/lineItems'
import type { components } from '../lib/api/schema'

type LineItem = components['schemas']['LineItemOut']

function applyPatch(item: LineItem, patch: LineItemPatch): LineItem {
  return {
    ...item,
    ...(patch.description !== undefined && { description: patch.description }),
    // Decimal fields are strings on LineItemOut — keep the optimistic merge type-consistent.
    ...(patch.total_price !== undefined && { total_price: String(patch.total_price) }),
    ...(patch.status !== undefined && { status: patch.status }),
    ...(patch.assigned_to !== undefined && { assigned_to: patch.assigned_to }),
  }
}

/**
 * Local-first line-item state: updates/deletes apply to `items` synchronously,
 * before the API call resolves, so the toggle/remove buttons feel instant; a
 * failed call rolls that one item back to its pre-edit snapshot. Reseeds from
 * `serverItems` (the receipt's authoritative line items) on every change, but
 * merges per-item rather than replacing wholesale — a slow edit on one item
 * can't be clobbered by a stale reload triggered by a faster edit on another.
 */
export function useOptimisticLineItems(serverItems: LineItem[]) {
  const [items, setItems] = useState(serverItems)
  const [error, setError] = useState<string | null>(null)
  const pendingUpdateIds = useRef(new Set<string>())
  const pendingDeleteIds = useRef(new Set<string>())

  useEffect(() => {
    setItems((current) =>
      serverItems
        .filter((s) => !pendingDeleteIds.current.has(s.id))
        .map((s) => (pendingUpdateIds.current.has(s.id) ? (current.find((c) => c.id === s.id) ?? s) : s)),
    )
  }, [serverItems])

  async function updateItem(itemId: string, patch: LineItemPatch): Promise<boolean> {
    const previous = items
    pendingUpdateIds.current.add(itemId)
    setItems((current) => current.map((it) => (it.id === itemId ? applyPatch(it, patch) : it)))
    setError(null)
    try {
      await lineItemsApi.updateLineItem(itemId, patch)
      return true
    } catch (err) {
      setItems(previous)
      setError(err instanceof Error ? err.message : 'Failed to save change')
      return false
    } finally {
      pendingUpdateIds.current.delete(itemId)
    }
  }

  async function deleteItem(itemId: string): Promise<boolean> {
    const previous = items
    pendingDeleteIds.current.add(itemId)
    setItems((current) => current.filter((it) => it.id !== itemId))
    setError(null)
    try {
      await lineItemsApi.deleteLineItem(itemId)
      return true
    } catch (err) {
      setItems(previous)
      setError(err instanceof Error ? err.message : 'Failed to remove item')
      return false
    } finally {
      pendingDeleteIds.current.delete(itemId)
    }
  }

  return { items, updateItem, deleteItem, error }
}
