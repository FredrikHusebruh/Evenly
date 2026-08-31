import { useContext } from 'react'
import { AuthContext } from './AuthContext'

export function useSession() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useSession must be used within an AuthProvider')
  return ctx
}
