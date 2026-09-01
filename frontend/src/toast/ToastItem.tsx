import { useEffect, useState } from 'react'
import { AlertCircle, CheckCircle2, X } from 'lucide-react'
import { IconButton } from '../components/IconButton'
import type { Toast } from './ToastContext'

export function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: (id: string) => void }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const raf = requestAnimationFrame(() => setVisible(true))
    return () => cancelAnimationFrame(raf)
  }, [])

  const shown = visible && !toast.leaving
  const isSuccess = toast.variant === 'success'
  const Icon = isSuccess ? CheckCircle2 : AlertCircle
  const tone = isSuccess ? 'border-accent/30 bg-accent-tint text-accent' : 'border-owed/30 bg-owed-tint text-owed'

  return (
    <div
      className={`flex items-center gap-2 rounded-md border px-3 py-2 text-sm shadow-sm transition-all duration-200 ${tone} ${
        shown ? 'translate-y-0 opacity-100' : 'translate-y-2 opacity-0'
      }`}
    >
      <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} />
      <span className="flex-1">{toast.message}</span>
      <IconButton icon={X} label="Dismiss" onClick={() => onDismiss(toast.id)} />
    </div>
  )
}
