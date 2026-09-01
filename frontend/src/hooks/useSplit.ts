import { useCallback, useEffect, useState } from 'react'
import * as splitApi from '../lib/api/split'
import type { components } from '../lib/api/schema'

type SplitResult = components['schemas']['SplitResult']

export function useSplit(receiptId: string, enabled: boolean) {
  const [split, setSplit] = useState<SplitResult | null>(null)
  const [loading, setLoading] = useState(true)

  const reload = useCallback(async () => {
    setLoading(true)
    try {
      setSplit(await splitApi.getReceiptSplit(receiptId))
    } finally {
      setLoading(false)
    }
  }, [receiptId])

  useEffect(() => {
    if (!enabled) return
    reload()
  }, [enabled, reload])

  return { split, loading, reload }
}
