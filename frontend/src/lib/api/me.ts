import { api, unwrap } from './client'

export async function getMe() {
  return unwrap(await api.GET('/api/v1/me'))
}

export async function updateMe(patch: { username: string | null }) {
  return unwrap(await api.PATCH('/api/v1/me', { body: patch }))
}
