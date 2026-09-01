import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { formatNok } from '../lib/format'
import type { components } from '../lib/api/schema'

type SpendingTrendPoint = components['schemas']['SpendingTrendPoint']

export function SpendingTrendChart({ data }: { data: SpendingTrendPoint[] }) {
  if (data.length === 0) return null

  const chartData = data.map((p) => ({ period: p.period, total: Number(p.total) }))

  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <h3 className="mb-3 text-sm font-medium text-muted">Spending over time</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={chartData} margin={{ left: 8, right: 16 }}>
          <CartesianGrid strokeDasharray="3 3" style={{ stroke: 'var(--color-border)' }} vertical={false} />
          <XAxis dataKey="period" style={{ fontSize: 12, fill: 'var(--color-muted)' }} />
          <YAxis tickFormatter={formatNok} width={70} style={{ fontSize: 12, fill: 'var(--color-muted)' }} />
          <Tooltip
            formatter={(value) => formatNok(Number(value))}
            contentStyle={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              fontSize: 12,
            }}
          />
          <Bar dataKey="total" style={{ fill: 'var(--color-accent)' }} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
