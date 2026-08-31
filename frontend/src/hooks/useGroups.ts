import { useCallback, useEffect, useState } from 'react'
import * as groupsApi from '../lib/api/groups'
import type { components } from '../lib/api/schema'

type Group = components['schemas']['GroupOut']

export function useGroups() {
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setGroups(await groupsApi.listGroups())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load groups')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    reload()
  }, [reload])

  async function createGroup(name: string) {
    const group = await groupsApi.createGroup(name)
    setGroups((prev) => [group, ...prev])
    return group
  }

  return { groups, loading, error, createGroup, reload }
}
