import { useCallback, useEffect, useState } from 'react'
import * as receiptsApi from '../lib/api/receipts'
import type { ReceiptFilters } from '../lib/api/receipts'
import type { components } from '../lib/api/schema'

type Receipt = components['schemas']['ReceiptOut']

export function useReceipts(groupId: string, filters: ReceiptFilters = {}) {
  const [receipts, setReceipts] = useState<Receipt[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { date_from, date_to, store, category_id } = filters

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setReceipts(await receiptsApi.listReceipts(groupId, { date_from, date_to, store, category_id }))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load receipts')
    } finally {
      setLoading(false)
    }
  }, [groupId, date_from, date_to, store, category_id])

  useEffect(() => {
    reload()
  }, [reload])

  return { receipts, loading, error, reload }
}
