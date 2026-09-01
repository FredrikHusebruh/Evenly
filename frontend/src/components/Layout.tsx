import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { Check, LogOut, Moon, Sun } from 'lucide-react'
import { supabase } from '../lib/supabaseClient'
import { useSession } from '../auth/useSession'
import { useTheme } from '../theme/useTheme'
import { useToast } from '../toast/useToast'
import * as meApi from '../lib/api/me'
import type { components } from '../lib/api/schema'
import { IconButton } from './IconButton'

type Me = components['schemas']['MeOut']

export function Layout({ children }: { children: ReactNode }) {
  const { session } = useSession()
  const { theme, toggleTheme } = useTheme()
  const { showToast } = useToast()
  const [me, setMe] = useState<Me | null>(null)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (session) meApi.getMe().then(setMe)
  }, [session])

  async function handleSave() {
    setSaving(true)
    try {
      const updated = await meApi.updateMe({ username: draft.trim() || null })
      setMe(updated)
      setEditing(false)
      showToast('Username updated')
    } catch {
      showToast('Failed to update username', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-2 px-4 py-3">
          <Link to="/groups" className="shrink-0 text-lg font-semibold tracking-tight">
            Evenly
          </Link>
          {session && me && (
            <div className="flex min-w-0 items-center gap-1">
              {editing ? (
                <div className="flex items-center gap-1.5">
                  <input
                    autoFocus
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSave()}
                    placeholder="Display name"
                    className="w-24 rounded-sm border border-border bg-surface px-2 py-1 text-sm outline-none focus:border-accent sm:w-32"
                  />
                  <IconButton icon={Check} label="Save display name" onClick={handleSave} disabled={saving} />
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => {
                    setDraft(me.username ?? '')
                    setEditing(true)
                  }}
                  className="max-w-[9rem] truncate text-sm text-muted hover:text-ink sm:max-w-none"
                  title="Click to set a display name"
                >
                  {me.username ?? me.email}
                </button>
              )}
              <IconButton
                icon={theme === 'dark' ? Sun : Moon}
                label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                onClick={toggleTheme}
              />
              <IconButton icon={LogOut} label="Sign out" onClick={() => supabase.auth.signOut()} />
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-8">{children}</main>
    </div>
  )
}
