-- Postgres RLS also gates INSERT ... RETURNING on the table's SELECT
-- policy. group creation inserts `groups` first and `group_members` (the
-- owner's own membership row) second, so at the moment the `groups` insert
-- returns its row, no membership exists yet and the original
-- is_group_member(id)-only SELECT policy rejects the RETURNING, failing
-- group creation outright. A group's creator should always be able to see
-- their own group regardless of membership-row timing, so widen the policy.

drop policy "members can view their groups" on public.groups;

create policy "members can view their groups"
  on public.groups for select
  using (public.is_group_member(id) or created_by = auth.uid());
