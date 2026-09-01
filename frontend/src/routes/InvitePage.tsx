import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import * as invitesApi from '../lib/api/invites'
import type { components } from '../lib/api/schema'
import { useSession } from '../auth/useSession'
import { Skeleton } from '../components/Skeleton'

type Preview = components['schemas']['InvitePreview']

export function InvitePage() {
  const { code } = useParams<{ code: string }>()
  const { session } = useSession()
  const [preview, setPreview] = useState<Preview | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [joining, setJoining] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    if (!code) return
    invitesApi
      .previewInvite(code)
      .then(setPreview)
      .catch((err) => setError(err instanceof Error ? err.message : 'Invite not found'))
  }, [code])

  async function handleJoin() {
    if (!code) return
    if (!session) {
      navigate(`/login?next=${encodeURIComponent(`/invite/${code}`)}`)
      return
    }
    setJoining(true)
    try {
      const group = await invitesApi.redeemInvite(code)
      navigate(`/groups/${group.id}`, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join')
      setJoining(false)
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-4 text-center">
      {error && <p className="text-sm text-owed">{error}</p>}
      {!error && !preview && (
        <div className="flex flex-col items-center gap-3">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-56" />
          <Skeleton className="h-11 w-full rounded-md" />
        </div>
      )}
      {preview && (
        <>
          <h1 className="mb-2 text-xl font-semibold tracking-tight">Join {preview.group_name}</h1>
          <p className="mb-6 text-sm text-muted">
            {preview.member_count} member{preview.member_count === 1 ? '' : 's'} already here.
          </p>
          <button
            type="button"
            onClick={handleJoin}
            disabled={joining}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover disabled:opacity-60"
          >
            {joining ? 'Joining…' : session ? 'Join group' : 'Log in to join'}
          </button>
        </>
      )}
    </div>
  )
}
