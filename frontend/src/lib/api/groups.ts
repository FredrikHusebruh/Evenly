import { api, unwrap } from './client'

export async function listGroups() {
  return unwrap(await api.GET('/api/v1/groups'))
}

export async function createGroup(name: string) {
  return unwrap(await api.POST('/api/v1/groups', { body: { name } }))
}

export async function getGroup(groupId: string) {
  return unwrap(await api.GET('/api/v1/groups/{group_id}', { params: { path: { group_id: groupId } } }))
}

export async function renameGroup(groupId: string, name: string) {
  return unwrap(
    await api.PATCH('/api/v1/groups/{group_id}', { params: { path: { group_id: groupId } }, body: { name } }),
  )
}

export async function deleteGroup(groupId: string) {
  await api.DELETE('/api/v1/groups/{group_id}', { params: { path: { group_id: groupId } } })
}

export async function removeMember(groupId: string, userId: string) {
  await api.DELETE('/api/v1/groups/{group_id}/members/{member_user_id}', {
    params: { path: { group_id: groupId, member_user_id: userId } },
  })
}
