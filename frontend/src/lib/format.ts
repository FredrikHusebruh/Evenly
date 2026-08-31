const nokFormatter = new Intl.NumberFormat('nb-NO', {
  style: 'currency',
  currency: 'NOK',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export function formatNok(amount: number | string): string {
  const value = typeof amount === 'string' ? Number(amount) : amount
  return nokFormatter.format(value)
}

export function formatDateNo(isoDate: string | null | undefined): string {
  if (!isoDate) return '—'
  return new Intl.DateTimeFormat('nb-NO', { day: 'numeric', month: 'short', year: 'numeric' }).format(
    new Date(isoDate),
  )
}
