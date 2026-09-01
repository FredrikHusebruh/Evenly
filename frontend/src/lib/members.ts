import type { components } from './api/schema'

type Member = components['schemas']['GroupMemberOut']

export function resolveMember(members: Member[], userId: string): Member | undefined {
  return members.find((m) => m.user_id === userId)
}

export function displayName(member: Member | undefined, userId: string, currentUserId: string | undefined): string {
  if (userId === currentUserId) return 'You'
  if (!member) return userId.slice(0, 8)
  return member.username || member.email || userId.slice(0, 8)
}
