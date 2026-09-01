import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { formatNok } from '../lib/format'
import type { components } from '../lib/api/schema'

type CategoryBreakdown = components['schemas']['CategoryBreakdown']

export function CategoryBreakdownChart({ data }: { data: CategoryBreakdown[] }) {
  if (data.length === 0) return null

  const chartData = data.map((c) => ({ name: c.category_name, total: Number(c.total) }))

  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <h3 className="mb-3 text-sm font-medium text-muted">Spending by category</h3>
      <ResponsiveContainer width="100%" height={Math.max(120, chartData.length * 40)}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16 }}>
          <CartesianGrid strokeDasharray="3 3" style={{ stroke: 'var(--color-border)' }} horizontal={false} />
          <XAxis type="number" tickFormatter={formatNok} style={{ fontSize: 12, fill: 'var(--color-muted)' }} />
          <YAxis type="category" dataKey="name" width={110} style={{ fontSize: 12, fill: 'var(--color-muted)' }} />
          <Tooltip
            formatter={(value) => formatNok(Number(value))}
            contentStyle={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              fontSize: 12,
            }}
          />
          <Bar dataKey="total" style={{ fill: 'var(--color-accent)' }} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
