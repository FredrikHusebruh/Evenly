import { useSettleUp } from '../hooks/useSettleUp'
import { Money } from './Money'

export function SettleUpTab({ groupId }: { groupId: string }) {
  const { settleUp, loading, error } = useSettleUp(groupId)

  if (loading) return <p className="text-sm text-muted">Loading…</p>
  if (error) return <p className="text-sm text-owed">{error}</p>
  if (!settleUp || settleUp.settlements.length === 0) {
    return <p className="text-sm text-muted">Everyone's settled up.</p>
  }

  return (
    <ul className="flex flex-col divide-y divide-border border-y border-border">
      {settleUp.settlements.map((settlement, i) => (
        <li key={i} className="flex items-center justify-between px-1 py-3 text-sm">
          <span>
            {settlement.from_user} owes {settlement.to_user}
          </span>
          <Money amount={settlement.amount} variant="owed" />
        </li>
      ))}
    </ul>
  )
}
