import { api, unwrap } from './client'

export async function getGroupAnalytics(groupId: string) {
  return unwrap(await api.GET('/api/v1/groups/{group_id}/analytics', { params: { path: { group_id: groupId } } }))
}
