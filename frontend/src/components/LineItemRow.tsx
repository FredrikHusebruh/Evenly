import { useState } from 'react'
import type { LineItemStatus } from '../lib/api/lineItems'
import type { components } from '../lib/api/schema'

type LineItem = components['schemas']['LineItemOut']
type GroupMember = components['schemas']['GroupMemberOut']

type LineItemPatch = {
  description?: string
  total_price?: number
  status?: LineItemStatus
  assigned_to?: string | null
}

const STATUSES: { key: LineItemStatus; label: string }[] = [
  { key: 'shared', label: 'Shared' },
  { key: 'personal', label: 'Personal' },
  { key: 'excluded', label: 'Excluded' },
]

export function LineItemRow({
  item,
  members,
  currentUserId,
  onUpdate,
  onDelete,
}: {
  item: LineItem
  members: GroupMember[]
  currentUserId: string | undefined
  onUpdate: (patch: LineItemPatch) => void
  onDelete: () => void
}) {
  const [description, setDescription] = useState(item.description)
  const [totalPrice, setTotalPrice] = useState(item.total_price)

  function memberLabel(userId: string) {
    return userId === currentUserId ? 'You' : userId.slice(0, 8)
  }

  return (
    <div className="flex flex-col gap-2 border-b border-border py-3 last:border-0">
      <div className="flex items-center gap-3">
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          onBlur={() => description !== item.description && onUpdate({ description })}
          className="flex-1 rounded-sm border border-transparent bg-transparent px-1 py-0.5 text-sm outline-none focus:border-border focus:bg-surface"
        />
        <input
          value={totalPrice}
          onChange={(e) => setTotalPrice(e.target.value)}
          onBlur={() => totalPrice !== item.total_price && onUpdate({ total_price: Number(totalPrice) })}
          className={`w-20 rounded-sm border border-transparent bg-transparent px-1 py-0.5 text-right text-sm tabular-nums outline-none focus:border-border focus:bg-surface ${
            item.status === 'excluded' ? 'text-muted line-through' : ''
          }`}
        />
        <button type="button" onClick={onDelete} className="text-xs text-muted hover:text-owed">
          Remove
        </button>
      </div>

      <div className="flex items-center gap-2">
        <div className="flex overflow-hidden rounded-sm border border-border text-xs">
          {STATUSES.map(({ key, label }) => (
            <button
              key={key}
              type="button"
              onClick={() => onUpdate({ status: key, assigned_to: key === 'personal' ? item.assigned_to : null })}
              className={`px-2 py-1 transition-colors ${
                item.status === key ? 'bg-accent text-white' : 'text-muted hover:bg-surface'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {item.status === 'personal' && (
          <select
            value={item.assigned_to ?? ''}
            onChange={(e) => onUpdate({ assigned_to: e.target.value || null })}
            className="rounded-sm border border-border bg-surface px-2 py-1 text-xs"
          >
            <option value="" disabled>
              Assign to…
            </option>
            {members.map((member) => (
              <option key={member.user_id} value={member.user_id}>
                {memberLabel(member.user_id)}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  )
}
