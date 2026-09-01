import { useCallback, useState, type ReactNode } from 'react'
import { ToastContext, type Toast, type ToastVariant } from './ToastContext'
import { ToastContainer } from './ToastContainer'

const DISPLAY_MS = 3000
const EXIT_MS = 200

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const dismiss = useCallback((id: string) => {
    setToasts((current) => current.map((t) => (t.id === id ? { ...t, leaving: true } : t)))
    setTimeout(() => {
      setToasts((current) => current.filter((t) => t.id !== id))
    }, EXIT_MS)
  }, [])

  const showToast = useCallback(
    (message: string, variant: ToastVariant = 'success') => {
      const id = crypto.randomUUID()
      setToasts((current) => [...current, { id, message, variant }])
      setTimeout(() => dismiss(id), DISPLAY_MS)
    },
    [dismiss],
  )

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  )
}
