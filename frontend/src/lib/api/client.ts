import createClient from 'openapi-fetch'
import type { paths } from './schema'
import { supabase } from '../supabaseClient'

// Paths in the generated schema already include the /api/v1 prefix (that's
// how FastAPI declares them), so baseUrl stays empty — setting it to
// '/api/v1' here would double it to /api/v1/api/v1/....
export const api = createClient<paths>({ baseUrl: '' })

api.use({
  async onRequest({ request }) {
    const {
      data: { session },
    } = await supabase.auth.getSession()
    if (session) {
      request.headers.set('Authorization', `Bearer ${session.access_token}`)
    }
    return request
  },
})

/** Throws on error, otherwise returns the typed data — keeps call sites free of error-shape checks. */
export function unwrap<T>(result: { data?: T; error?: unknown }): T {
  if (result.error !== undefined) {
    const detail =
      typeof result.error === 'object' && result.error !== null && 'detail' in result.error
        ? String((result.error as { detail: unknown }).detail)
        : 'Request failed'
    throw new Error(detail)
  }
  return result.data as T
}
