import { CheckCircle2 } from 'lucide-react'
import { useSettleUp } from '../hooks/useSettleUp'
import { Money } from './Money'
import { Skeleton } from './Skeleton'
import { EmptyState } from './EmptyState'
import { displayName, resolveMember } from '../lib/members'
import type { components } from '../lib/api/schema'

type GroupMember = components['schemas']['GroupMemberOut']

export function SettleUpTab({
  groupId,
  members,
  currentUserId,
}: {
  groupId: string
  members: GroupMember[]
  currentUserId: string | undefined
}) {
  const { settleUp, loading, error } = useSettleUp(groupId)

  if (loading) {
    return (
      <div className="flex flex-col divide-y divide-border border-y border-border">
        {[0, 1].map((i) => (
          <div key={i} className="flex items-center justify-between px-1 py-3">
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-4 w-16" />
          </div>
        ))}
      </div>
    )
  }
  if (error) return <p className="text-sm text-owed">{error}</p>
  if (!settleUp || settleUp.settlements.length === 0) {
    return <EmptyState icon={CheckCircle2} title="Everyone's settled up." tone="positive" />
  }

  return (
    <ul className="flex flex-col divide-y divide-border border-y border-border">
      {settleUp.settlements.map((settlement, i) => (
        <li key={i} className="flex items-center justify-between px-1 py-3 text-sm">
          <span>
            {displayName(resolveMember(members, settlement.from_user), settlement.from_user, currentUserId)} owes{' '}
            {displayName(resolveMember(members, settlement.to_user), settlement.to_user, currentUserId)}
          </span>
          <Money amount={settlement.amount} variant="owed" />
        </li>
      ))}
    </ul>
  )
}
