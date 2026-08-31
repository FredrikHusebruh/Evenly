import { api, unwrap } from './client'

export async function listCategories(groupId: string) {
  return unwrap(await api.GET('/api/v1/groups/{group_id}/categories', { params: { path: { group_id: groupId } } }))
}

export async function createCategory(groupId: string, name: string) {
  return unwrap(
    await api.POST('/api/v1/groups/{group_id}/categories', {
      params: { path: { group_id: groupId } },
      body: { name },
    }),
  )
}
