import { useCallback, useEffect, useState } from 'react'
import * as analyticsApi from '../lib/api/analytics'
import type { components } from '../lib/api/schema'

type GroupAnalytics = components['schemas']['GroupAnalyticsOut']

export function useAnalytics(groupId: string) {
  const [analytics, setAnalytics] = useState<GroupAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setAnalytics(await analyticsApi.getGroupAnalytics(groupId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics')
    } finally {
      setLoading(false)
    }
  }, [groupId])

  useEffect(() => {
    reload()
  }, [reload])

  return { analytics, loading, error, reload }
}
