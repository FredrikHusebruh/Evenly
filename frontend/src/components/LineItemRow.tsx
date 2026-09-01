import { useState } from 'react'
import type { LineItemPatch, LineItemStatus } from '../lib/api/lineItems'
import type { components } from '../lib/api/schema'
import { displayName } from '../lib/members'

type LineItem = components['schemas']['LineItemOut']
type GroupMember = components['schemas']['GroupMemberOut']

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
  // Clicking "Personal" only stages the assignee picker — it never patches the
  // server until a member is actually chosen, so a personal item can never be
  // saved without an assignee (an unassigned personal item silently drops its
  // cost out of every member's split total).
  const [pendingPersonal, setPendingPersonal] = useState(false)

  const showAssigneePicker = item.status === 'personal' || pendingPersonal

  function handleStatusClick(key: LineItemStatus) {
    if (key === 'personal') {
      if (item.status === 'personal' && item.assigned_to) return
      setPendingPersonal(true)
      return
    }
    setPendingPersonal(false)
    onUpdate({ status: key, assigned_to: null })
  }

  function handleAssigneeChange(userId: string) {
    setPendingPersonal(false)
    onUpdate({ status: 'personal', assigned_to: userId })
  }

  return (
    <div className="flex flex-col gap-1.5 border-b border-dashed border-border py-2.5 font-mono text-sm last:border-0">
      <div className="flex items-center gap-3">
        {Number(item.quantity) !== 1 && <span className="shrink-0 text-muted">{item.quantity}×</span>}
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          onBlur={() => description !== item.description && onUpdate({ description })}
          className="min-w-0 flex-1 rounded-sm border border-transparent bg-transparent px-1 py-0.5 uppercase outline-none focus:border-border focus:bg-surface"
        />
        <input
          value={totalPrice}
          onChange={(e) => setTotalPrice(e.target.value)}
          onBlur={() => totalPrice !== item.total_price && onUpdate({ total_price: Number(totalPrice) })}
          className={`w-16 shrink-0 rounded-sm border border-transparent bg-transparent px-1 py-0.5 text-right tabular-nums outline-none focus:border-border focus:bg-surface ${
            item.status === 'excluded' ? 'text-muted line-through' : ''
          }`}
        />
        <button type="button" onClick={onDelete} className="shrink-0 text-xs text-muted hover:text-owed">
          ✕
        </button>
      </div>

      <div className="flex items-center gap-2 text-xs">
        <div className="flex overflow-hidden rounded-sm border border-border">
          {STATUSES.map(({ key, label }) => (
            <button
              key={key}
              type="button"
              onClick={() => handleStatusClick(key)}
              className={`px-2 py-1 uppercase tracking-wide transition-colors ${
                (key === 'personal' ? showAssigneePicker : item.status === key)
                  ? 'bg-accent text-white'
                  : 'text-muted hover:bg-surface'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {showAssigneePicker && (
          <select
            value={item.status === 'personal' ? (item.assigned_to ?? '') : ''}
            onChange={(e) => handleAssigneeChange(e.target.value)}
            className="rounded-sm border border-border bg-surface px-2 py-1"
          >
            <option value="" disabled>
              Assign to…
            </option>
            {members.map((member) => (
              <option key={member.user_id} value={member.user_id}>
                {displayName(member, member.user_id, currentUserId)}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  )
}
