import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { supabase } from '../lib/supabaseClient'
import { useSession } from '../auth/useSession'

export function Layout({ children }: { children: ReactNode }) {
  const { session } = useSession()

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
          <Link to="/groups" className="text-lg font-semibold tracking-tight">
            Evenly
          </Link>
          {session && (
            <button
              type="button"
              onClick={() => supabase.auth.signOut()}
              className="text-sm text-muted hover:text-ink"
            >
              Sign out
            </button>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-8">{children}</main>
    </div>
  )
}
