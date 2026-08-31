import { api, unwrap } from './client'

export async function createInvite(groupId: string) {
  return unwrap(
    await api.POST('/api/v1/groups/{group_id}/invites', { params: { path: { group_id: groupId } }, body: {} }),
  )
}

export async function listInvites(groupId: string) {
  return unwrap(await api.GET('/api/v1/groups/{group_id}/invites', { params: { path: { group_id: groupId } } }))
}

export async function revokeInvite(groupId: string, inviteId: string) {
  await api.DELETE('/api/v1/groups/{group_id}/invites/{invite_id}', {
    params: { path: { group_id: groupId, invite_id: inviteId } },
  })
}

export async function previewInvite(code: string) {
  return unwrap(await api.GET('/api/v1/invites/{code}', { params: { path: { code } } }))
}

export async function redeemInvite(code: string) {
  return unwrap(await api.POST('/api/v1/invites/{code}/redeem', { params: { path: { code } } }))
}
