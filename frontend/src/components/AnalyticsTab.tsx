import { BarChart3 } from 'lucide-react'
import { useAnalytics } from '../hooks/useAnalytics'
import { Money } from './Money'
import { Skeleton } from './Skeleton'
import { EmptyState } from './EmptyState'
import { CategoryBreakdownChart } from './CategoryBreakdownChart'
import { SpendingTrendChart } from './SpendingTrendChart'
import { MemberHistoryChart } from './MemberHistoryChart'
import { TopListsPanel } from './TopListsPanel'

export function AnalyticsTab({ groupId }: { groupId: string }) {
  const { analytics, loading, error } = useAnalytics(groupId)

  if (loading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-16 w-full rounded-md" />
        <Skeleton className="h-40 w-full rounded-md" />
        <Skeleton className="h-40 w-full rounded-md" />
        <Skeleton className="h-40 w-full rounded-md" />
      </div>
    )
  }
  if (error) return <p className="text-sm text-owed">{error}</p>
  if (!analytics) return null

  if (analytics.receipt_count === 0) {
    return (
      <EmptyState icon={BarChart3} title="No receipts yet — analytics will show up once this group has some." />
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-baseline justify-between rounded-md border border-border bg-surface p-4">
        <span className="text-sm text-muted">Total spent</span>
        <div className="flex items-baseline gap-2">
          <Money amount={analytics.total_spent} className="text-lg font-semibold" />
          <span className="text-xs text-muted">
            across {analytics.receipt_count} receipt{analytics.receipt_count === 1 ? '' : 's'}
          </span>
        </div>
      </div>

      <CategoryBreakdownChart data={analytics.category_breakdown} />
      <SpendingTrendChart data={analytics.spending_trend} />
      <MemberHistoryChart data={analytics.member_history} />
      <TopListsPanel
        items={analytics.top_items}
        merchants={analytics.top_merchants}
        receipts={analytics.top_receipts}
      />
    </div>
  )
}
