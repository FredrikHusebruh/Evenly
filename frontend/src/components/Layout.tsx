import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { supabase } from '../lib/supabaseClient'
import { useSession } from '../auth/useSession'
import * as meApi from '../lib/api/me'
import type { components } from '../lib/api/schema'

type Me = components['schemas']['MeOut']

export function Layout({ children }: { children: ReactNode }) {
  const { session } = useSession()
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
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
          <Link to="/groups" className="text-lg font-semibold tracking-tight">
            Evenly
          </Link>
          {session && me && (
            <div className="flex items-center gap-4">
              {editing ? (
                <div className="flex items-center gap-2">
                  <input
                    autoFocus
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSave()}
                    placeholder="Display name"
                    className="w-32 rounded-sm border border-border bg-surface px-2 py-1 text-sm outline-none focus:border-accent"
                  />
                  <button
                    type="button"
                    onClick={handleSave}
                    disabled={saving}
                    className="text-sm text-accent hover:text-accent-hover disabled:opacity-60"
                  >
                    {saving ? 'Saving…' : 'Save'}
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => {
                    setDraft(me.username ?? '')
                    setEditing(true)
                  }}
                  className="text-sm text-muted hover:text-ink"
                  title="Click to set a display name"
                >
                  {me.username ?? me.email}
                </button>
              )}
              <button
                type="button"
                onClick={() => supabase.auth.signOut()}
                className="text-sm text-muted hover:text-ink"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-8">{children}</main>
    </div>
  )
}
