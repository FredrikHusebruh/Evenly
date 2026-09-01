import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import { Copy, Link2 } from 'lucide-react'
import * as groupsApi from '../lib/api/groups'
import * as invitesApi from '../lib/api/invites'
import { displayName } from '../lib/members'
import { useToast } from '../toast/useToast'
import { IconButton } from './IconButton'
import { EmptyState } from './EmptyState'
import type { components } from '../lib/api/schema'

type GroupDetail = components['schemas']['GroupDetail']
type Invite = components['schemas']['InviteOut']

export function MembersTab({
  group,
  isOwner,
  currentUserId,
  onChange,
}: {
  group: GroupDetail
  isOwner: boolean
  currentUserId: string | undefined
  onChange: () => void
}) {
  const [invites, setInvites] = useState<Invite[]>([])
  const [creating, setCreating] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const { showToast } = useToast()
  const navigate = useNavigate()

  useEffect(() => {
    if (!isOwner) return
    invitesApi.listInvites(group.id).then(setInvites)
  }, [group.id, isOwner])

  async function handleCreateInvite() {
    setCreating(true)
    try {
      const invite = await invitesApi.createInvite(group.id)
      setInvites((prev) => [invite, ...prev])
      showToast('Invite created')
    } catch {
      showToast('Failed to create invite', 'error')
    } finally {
      setCreating(false)
    }
  }

  async function handleRevoke(inviteId: string) {
    await invitesApi.revokeInvite(group.id, inviteId)
    setInvites((prev) => prev.filter((i) => i.id !== inviteId))
  }

  async function handleRemove(userId: string) {
    await groupsApi.removeMember(group.id, userId)
    onChange()
    showToast('Member removed')
  }

  async function handleCopy(code: string) {
    try {
      await navigator.clipboard.writeText(code)
      showToast('Invite code copied')
    } catch {
      showToast('Failed to copy code', 'error')
    }
  }

  async function handleDeleteGroup() {
    if (!window.confirm(`Delete "${group.name}"? This permanently removes all its receipts and cannot be undone.`)) {
      return
    }
    setDeleting(true)
    try {
      await groupsApi.deleteGroup(group.id)
      showToast('Group deleted')
      navigate('/groups')
    } catch {
      showToast('Failed to delete group', 'error')
      setDeleting(false)
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <ul className="flex flex-col divide-y divide-border border-y border-border">
        {group.members.map((member) => (
          <li key={member.user_id} className="flex items-center justify-between px-1 py-3 text-sm">
            <span>
              {displayName(member, member.user_id, currentUserId)}{' '}
              {member.role === 'owner' && <span className="text-muted">· owner</span>}
            </span>
            {isOwner && member.role !== 'owner' && (
              <button
                type="button"
                onClick={() => handleRemove(member.user_id)}
                className="text-muted hover:text-owed"
              >
                Remove
              </button>
            )}
          </li>
        ))}
      </ul>

      {isOwner && (
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-muted">Invite links</h2>
            <button
              type="button"
              onClick={handleCreateInvite}
              disabled={creating}
              className="rounded-md border border-border px-3 py-1.5 text-sm transition-colors hover:border-accent disabled:opacity-60"
            >
              {creating ? 'Creating…' : 'New invite'}
            </button>
          </div>
          {invites.length === 0 ? (
            <EmptyState icon={Link2} title="No active invites." compact />
          ) : (
            <ul className="flex flex-col divide-y divide-border">
              {invites.map((invite) => (
                <li key={invite.id} className="flex items-center justify-between py-2 text-sm">
                  <span className="flex items-center gap-1">
                    <span className="tabular-nums">{invite.code}</span>
                    <IconButton icon={Copy} label="Copy invite code" onClick={() => handleCopy(invite.code)} />
                  </span>
                  <button
                    type="button"
                    onClick={() => handleRevoke(invite.id)}
                    className="text-muted hover:text-owed"
                  >
                    Revoke
                  </button>
                </li>
              ))}
            </ul>
          )}

          <div className="flex items-center justify-between rounded-md border border-owed/30 bg-owed-tint px-3 py-2.5">
            <span className="text-sm text-owed">Delete this group and all its receipts.</span>
            <button
              type="button"
              onClick={handleDeleteGroup}
              disabled={deleting}
              className="shrink-0 rounded-md border border-owed/40 px-3 py-1.5 text-sm text-owed transition-colors hover:bg-owed/10 disabled:opacity-60"
            >
              {deleting ? 'Deleting…' : 'Delete group'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
