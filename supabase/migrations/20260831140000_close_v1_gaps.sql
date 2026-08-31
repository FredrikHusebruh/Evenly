-- Phase 1-2 gap closure: line-item state, receipt currency/OCR status,
-- group invites, is_group_owner() helper, and missing UPDATE/DELETE policies.
-- Purely additive except for the group_members INSERT policy fix below,
-- which corrects a bug that makes it impossible for a group's creator to
-- ever become its first member.

-- 1. line_items: explicit shared/personal/excluded state -------------------

alter table public.line_items
  add column status text not null default 'shared'
    check (status in ('shared', 'personal', 'excluded')),
  add column assigned_to uuid references auth.users (id) on delete set null,
  add constraint line_items_personal_requires_assignee
    check ((status = 'personal') = (assigned_to is not null));

-- 2. receipts: currency default + OCR status scaffold -----------------------

alter table public.receipts
  alter column currency set default 'NOK',
  add column ocr_status text not null default 'pending'
    check (ocr_status in ('pending', 'processing', 'succeeded', 'failed')),
  add column ocr_error text;

-- 3. group_invites -----------------------------------------------------------

create table public.group_invites (
  id uuid primary key default gen_random_uuid(),
  group_id uuid not null references public.groups (id) on delete cascade,
  code text not null unique,
  created_by uuid not null references auth.users (id) on delete cascade,
  created_at timestamptz not null default now(),
  expires_at timestamptz,
  revoked_at timestamptz,
  max_uses integer,
  use_count integer not null default 0
);

create index on public.group_invites (group_id);

alter table public.group_invites enable row level security;

create policy "members can view their group's invites"
  on public.group_invites for select
  using (public.is_group_member(group_id));

-- No insert/update/delete policies for authenticated clients: invite
-- creation, revocation, preview, and redemption all go through the backend's
-- service-role client, since a code is a bearer credential whose validity
-- (expiry/revocation/max-uses) can't be expressed as a row-security predicate
-- keyed on auth.uid().

-- 4. is_group_owner() helper --------------------------------------------------

create or replace function public.is_group_owner(target_group_id uuid)
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists (
    select 1 from public.group_members
    where group_id = target_group_id and user_id = auth.uid() and role = 'owner'
  );
$$;

-- 5. groups: update/delete ----------------------------------------------------

create policy "owners can update their group"
  on public.groups for update
  using (public.is_group_owner(id))
  with check (public.is_group_owner(id));

create policy "owners can delete their group"
  on public.groups for delete
  using (public.is_group_owner(id));

-- 6. group_members: fix the broken insert policy + add update/delete ---------

drop policy "owners can manage membership" on public.group_members;

create policy "creator can self-insert as owner"
  on public.group_members for insert
  with check (
    user_id = auth.uid() and role = 'owner'
    and exists (select 1 from public.groups where id = group_id and created_by = auth.uid())
  );

create policy "owners can update membership"
  on public.group_members for update
  using (public.is_group_owner(group_id))
  with check (public.is_group_owner(group_id));

create policy "leave or be removed"
  on public.group_members for delete
  using (user_id = auth.uid() or public.is_group_owner(group_id));

-- 7. categories: update/delete ------------------------------------------------

create policy "members can update categories"
  on public.categories for update
  using (public.is_group_member(group_id))
  with check (public.is_group_member(group_id));

create policy "members can delete categories"
  on public.categories for delete
  using (public.is_group_member(group_id));

-- 8. receipts: update/delete --------------------------------------------------

create policy "members can update receipts"
  on public.receipts for update
  using (public.is_group_member(group_id))
  with check (public.is_group_member(group_id));

create policy "uploader or owner can delete receipts"
  on public.receipts for delete
  using (uploaded_by = auth.uid() or public.is_group_owner(group_id));

-- 9. line_items: update/delete -------------------------------------------------

create policy "members can update line items"
  on public.line_items for update
  using (
    exists (
      select 1 from public.receipts
      where receipts.id = line_items.receipt_id
        and public.is_group_member(receipts.group_id)
    )
  )
  with check (
    exists (
      select 1 from public.receipts
      where receipts.id = line_items.receipt_id
        and public.is_group_member(receipts.group_id)
    )
  );

create policy "members can delete line items"
  on public.line_items for delete
  using (
    exists (
      select 1 from public.receipts
      where receipts.id = line_items.receipt_id
        and public.is_group_member(receipts.group_id)
    )
  );

-- 10. item_assignments: update/delete -------------------------------------------

create policy "members can update item assignments"
  on public.item_assignments for update
  using (
    exists (
      select 1 from public.line_items
      join public.receipts on receipts.id = line_items.receipt_id
      where line_items.id = item_assignments.line_item_id
        and public.is_group_member(receipts.group_id)
    )
  )
  with check (
    exists (
      select 1 from public.line_items
      join public.receipts on receipts.id = line_items.receipt_id
      where line_items.id = item_assignments.line_item_id
        and public.is_group_member(receipts.group_id)
    )
  );

create policy "members can delete item assignments"
  on public.item_assignments for delete
  using (
    exists (
      select 1 from public.line_items
      join public.receipts on receipts.id = line_items.receipt_id
      where line_items.id = item_assignments.line_item_id
        and public.is_group_member(receipts.group_id)
    )
  );

-- 11. storage.objects: delete policy for the receipts bucket -------------------

create policy "members can delete their group's receipt images"
  on storage.objects for delete
  using (
    bucket_id = 'receipts'
    and public.is_group_member((storage.foldername(name))[1]::uuid)
  );
