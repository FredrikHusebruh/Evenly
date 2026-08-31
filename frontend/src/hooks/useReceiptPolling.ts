import { useCallback, useEffect, useState } from 'react'
import * as receiptsApi from '../lib/api/receipts'
import type { components } from '../lib/api/schema'

type ReceiptDetail = components['schemas']['ReceiptDetail']

const POLL_INTERVAL_MS = 2000

export function useReceiptPolling(receiptId: string) {
  const [receipt, setReceipt] = useState<ReceiptDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    try {
      setReceipt(await receiptsApi.getReceipt(receiptId))
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load receipt')
    } finally {
      setLoading(false)
    }
  }, [receiptId])

  useEffect(() => {
    reload()
  }, [reload])

  useEffect(() => {
    if (!receipt || (receipt.ocr_status !== 'pending' && receipt.ocr_status !== 'processing')) return
    const interval = setInterval(reload, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [receipt, reload])

  return { receipt, loading, error, reload }
}
