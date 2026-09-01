import { Money } from './Money'
import { displayName, resolveMember } from '../lib/members'
import type { components } from '../lib/api/schema'

type SplitResult = components['schemas']['SplitResult']
type GroupMember = components['schemas']['GroupMemberOut']

export function SplitSummaryPanel({
  split,
  members,
  currentUserId,
  loading = false,
}: {
  split: SplitResult
  members: GroupMember[]
  currentUserId: string | undefined
  loading?: boolean
}) {
  return (
    <div className={`rounded-md border border-border bg-surface p-4 ${loading ? 'animate-pulse' : ''}`}>
      <div className="mb-3 flex justify-between text-sm">
        <span className="text-muted">Shared total</span>
        <Money amount={split.shared_total} />
      </div>
      {Number(split.excluded_total) > 0 && (
        <div className="mb-3 flex justify-between text-sm text-muted">
          <span>Excluded</span>
          <Money amount={split.excluded_total} />
        </div>
      )}
      <div className="flex flex-col divide-y divide-border border-t border-border pt-2">
        {split.member_splits.map((member) => (
          <div key={member.user_id} className="flex justify-between py-2 text-sm">
            <span>{displayName(resolveMember(members, member.user_id), member.user_id, currentUserId)}</span>
            <Money amount={member.owed_total} variant={Number(member.owed_total) !== 0 ? 'owed' : 'neutral'} />
          </div>
        ))}
      </div>
    </div>
  )
}
