import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY')
}

// Used only for auth session management and direct-to-storage receipt image
// uploads. Everything with business logic goes through the typed API client
// to FastAPI instead, even where RLS would technically permit a direct call.
export const supabase = createClient(supabaseUrl, supabaseAnonKey)
