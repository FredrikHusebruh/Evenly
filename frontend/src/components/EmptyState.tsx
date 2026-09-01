import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

export function EmptyState({
  icon: Icon,
  title,
  action,
  compact = false,
  tone = 'neutral',
}: {
  icon: LucideIcon
  title: string
  action?: ReactNode
  compact?: boolean
  tone?: 'neutral' | 'positive'
}) {
  const color = tone === 'positive' ? 'text-accent' : 'text-muted'
  return (
    <div className={`flex flex-col items-center gap-2 text-center ${compact ? 'py-4' : 'py-10'}`}>
      <Icon className={`${compact ? 'h-5 w-5' : 'h-8 w-8'} ${color}`} strokeWidth={1.5} />
      <p className={`text-sm ${color}`}>{title}</p>
      {action}
    </div>
  )
}
