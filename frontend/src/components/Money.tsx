import { formatNok } from '../lib/format'

type MoneyProps = {
  amount: number | string
  variant?: 'neutral' | 'owed' | 'settled'
  className?: string
}

const variantClass: Record<NonNullable<MoneyProps['variant']>, string> = {
  neutral: '',
  owed: 'text-owed',
  settled: 'text-accent',
}

/** Centralizes tabular-nums so every rendered amount aligns consistently — this is a receipts app, misaligned prices are not acceptable. */
export function Money({ amount, variant = 'neutral', className = '' }: MoneyProps) {
  return <span className={`tabular-nums ${variantClass[variant]} ${className}`.trim()}>{formatNok(amount)}</span>
}
