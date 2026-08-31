import { useCallback, useEffect, useState } from 'react'
import * as groupsApi from '../lib/api/groups'
import type { components } from '../lib/api/schema'

type GroupDetail = components['schemas']['GroupDetail']

export function useGroupDetail(groupId: string) {
  const [group, setGroup] = useState<GroupDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setGroup(await groupsApi.getGroup(groupId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load group')
    } finally {
      setLoading(false)
    }
  }, [groupId])

  useEffect(() => {
    reload()
  }, [reload])

  return { group, loading, error, reload }
}
