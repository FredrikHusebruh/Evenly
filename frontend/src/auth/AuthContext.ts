import type { Session } from '@supabase/supabase-js'
import { createContext } from 'react'

export type AuthContextValue = {
  session: Session | null
  loading: boolean
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)
