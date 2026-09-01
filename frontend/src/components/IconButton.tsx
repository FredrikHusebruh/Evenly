import type { ButtonHTMLAttributes } from 'react'
import type { LucideIcon } from 'lucide-react'

type IconButtonProps = {
  icon: LucideIcon
  label: string
  variant?: 'default' | 'danger'
  size?: 'default' | 'sm'
} & ButtonHTMLAttributes<HTMLButtonElement>

const SIZES = {
  default: { button: 'h-9 w-9', icon: 'h-[18px] w-[18px]' },
  sm: { button: 'h-7 w-7', icon: 'h-4 w-4' },
}

export function IconButton({
  icon: Icon,
  label,
  variant = 'default',
  size = 'default',
  className = '',
  ...rest
}: IconButtonProps) {
  const tone = variant === 'danger' ? 'text-muted hover:text-owed' : 'text-muted hover:text-ink'
  const { button, icon } = SIZES[size]
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={`inline-flex shrink-0 items-center justify-center rounded-md transition-colors focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-2 disabled:opacity-60 ${button} ${tone} ${className}`.trim()}
      {...rest}
    >
      <Icon className={icon} strokeWidth={1.75} />
    </button>
  )
}
