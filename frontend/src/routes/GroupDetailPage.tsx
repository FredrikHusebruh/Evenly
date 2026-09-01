import { useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { useGroupDetail } from '../hooks/useGroupDetail'
import { useReceipts } from '../hooks/useReceipts'
import { ReceiptHistoryTable } from '../components/ReceiptHistoryTable'
import { MembersTab } from '../components/MembersTab'
import { SettleUpTab } from '../components/SettleUpTab'
import { AnalyticsTab } from '../components/AnalyticsTab'
import { useSession } from '../auth/useSession'

type Tab = 'receipts' | 'members' | 'settle' | 'analytics'

export function GroupDetailPage() {
  const { groupId } = useParams<{ groupId: string }>()
  const { session } = useSession()
  const { group, loading, error, reload } = useGroupDetail(groupId!)
  const { receipts, loading: receiptsLoading } = useReceipts(groupId!)
  const [tab, setTab] = useState<Tab>('receipts')
  const navigate = useNavigate()

  if (loading) return <p className="text-sm text-muted">Loading…</p>
  if (error || !group) return <p className="text-sm text-owed">{error ?? 'Group not found'}</p>

  const isOwner = group.members.find((m) => m.user_id === session?.user.id)?.role === 'owner'

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">{group.name}</h1>
        <button
          type="button"
          onClick={() => navigate(`/groups/${groupId}/receipts/new`)}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover"
        >
          Add receipt
        </button>
      </div>

      <nav className="flex gap-6 border-b border-border text-sm">
        {(
          [
            ['receipts', 'Receipts'],
            ['members', 'Members'],
            ['settle', 'Settle up'],
            ['analytics', 'Analytics'],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`-mb-px border-b-2 pb-2 ${
              tab === key ? 'border-accent text-ink' : 'border-transparent text-muted hover:text-ink'
            }`}
          >
            {label}
          </button>
        ))}
      </nav>

      {tab === 'receipts' &&
        (receiptsLoading ? (
          <p className="text-sm text-muted">Loading…</p>
        ) : (
          <ReceiptHistoryTable groupId={groupId!} receipts={receipts} />
        ))}
      {tab === 'members' && (
        <MembersTab group={group} isOwner={isOwner} currentUserId={session?.user.id} onChange={reload} />
      )}
      {tab === 'settle' && (
        <SettleUpTab groupId={groupId!} members={group.members} currentUserId={session?.user.id} />
      )}
      {tab === 'analytics' && <AnalyticsTab groupId={groupId!} />}
    </div>
  )
}
