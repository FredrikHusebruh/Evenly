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
    <div className={`mt-2 border-t-4 border-double border-ink pt-3 font-mono text-sm ${loading ? 'animate-pulse' : ''}`}>
      <div className="flex justify-between uppercase tracking-wide text-muted">
        <span>Subtotal (shared)</span>
        <Money amount={split.shared_total} />
      </div>
      {Number(split.excluded_total) > 0 && (
        <div className="mt-1 flex justify-between uppercase tracking-wide text-muted">
          <span>Excluded</span>
          <Money amount={split.excluded_total} />
        </div>
      )}
      <div className="mt-2 flex flex-col gap-1.5 border-t border-dashed border-border pt-2">
        {split.member_splits.map((member) => (
          <div key={member.user_id} className="flex justify-between uppercase">
            <span>{displayName(resolveMember(members, member.user_id), member.user_id, currentUserId)}</span>
            <Money amount={member.owed_total} variant={Number(member.owed_total) !== 0 ? 'owed' : 'neutral'} />
          </div>
        ))}
      </div>
    </div>
  )
}
