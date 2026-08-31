-- Same class of bug as the groups-select-own fix: group_members' SELECT
-- policy checks membership via a subquery against group_members itself,
-- and that self-referential subquery does not see the row being inserted
-- by the same statement, so INSERT ... RETURNING on a member's own
-- bootstrap row fails RLS even though the INSERT's WITH CHECK passed. A
-- user should always be able to see their own membership row directly
-- (a simple column comparison needs no subquery, so it works immediately).

drop policy "members can view group membership" on public.group_members;

create policy "members can view group membership"
  on public.group_members for select
  using (public.is_group_member(group_id) or user_id = auth.uid());
