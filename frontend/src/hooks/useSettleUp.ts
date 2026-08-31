import { useEffect, useState } from 'react'
import * as splitApi from '../lib/api/split'
import type { components } from '../lib/api/schema'

type SettleUp = components['schemas']['SettleUpOut']

export function useSettleUp(groupId: string) {
  const [settleUp, setSettleUp] = useState<SettleUp | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    splitApi
      .getSettleUp(groupId)
      .then(setSettleUp)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load settle-up'))
      .finally(() => setLoading(false))
  }, [groupId])

  return { settleUp, loading, error }
}
