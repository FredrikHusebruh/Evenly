import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { Users } from 'lucide-react'
import { useGroups } from '../hooks/useGroups'
import { Skeleton } from '../components/Skeleton'
import { EmptyState } from '../components/EmptyState'

export function GroupsPage() {
  const { groups, loading, error, createGroup } = useGroups()
  const [name, setName] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [code, setCode] = useState('')
  const navigate = useNavigate()

  async function handleCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!name.trim()) return
    setCreating(true)
    setCreateError(null)
    try {
      const group = await createGroup(name.trim())
      setName('')
      navigate(`/groups/${group.id}`)
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create group')
    } finally {
      setCreating(false)
    }
  }

  function handleJoin(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!code.trim()) return
    navigate(`/invite/${code.trim()}`)
  }

  return (
    <div className="flex flex-col gap-12">
      <section>
        <h1 className="mb-6 text-xl font-semibold tracking-tight">Your groups</h1>
        {error && <p className="text-sm text-owed">{error}</p>}
        {loading ? (
          <div className="flex flex-col divide-y divide-border border-y border-border">
            {[0, 1, 2].map((i) => (
              <div key={i} className="px-1 py-3">
                <Skeleton className="h-5 w-40" />
              </div>
            ))}
          </div>
        ) : groups.length === 0 ? (
          <EmptyState icon={Users} title="No groups yet — create one below." />
        ) : (
          <ul className="flex flex-col divide-y divide-border border-y border-border">
            {groups.map((group) => (
              <li key={group.id}>
                <a
                  href={`/groups/${group.id}`}
                  onClick={(e) => {
                    e.preventDefault()
                    navigate(`/groups/${group.id}`)
                  }}
                  className="block px-1 py-3 text-base hover:text-accent"
                >
                  {group.name}
                </a>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="grid gap-8 sm:grid-cols-2">
        <form onSubmit={handleCreate} className="flex flex-col gap-3">
          <h2 className="text-sm font-medium text-muted">Create a group</h2>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Cabin trip"
            className="rounded-sm border border-border bg-surface px-3 py-2 text-base outline-none focus:border-accent"
          />
          <button
            type="submit"
            disabled={creating || !name.trim()}
            className="self-start rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover disabled:opacity-60"
          >
            {creating ? 'Creating…' : 'Create group'}
          </button>
          {createError && <p className="text-sm text-owed">{createError}</p>}
        </form>

        <form onSubmit={handleJoin} className="flex flex-col gap-3">
          <h2 className="text-sm font-medium text-muted">Join via code</h2>
          <input
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            placeholder="Invite code"
            className="rounded-sm border border-border bg-surface px-3 py-2 text-base uppercase outline-none focus:border-accent"
          />
          <button
            type="submit"
            disabled={!code.trim()}
            className="self-start rounded-md border border-border px-4 py-2 text-sm font-medium transition-colors hover:border-accent disabled:opacity-60"
          >
            Preview invite
          </button>
        </form>
      </section>
    </div>
  )
}
