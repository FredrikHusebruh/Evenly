-- Receipt Splitter initial schema
-- Users are handled by Supabase Auth (auth.users); everything below references auth.uid().

create table public.groups (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_by uuid not null references auth.users (id) on delete cascade,
  created_at timestamptz not null default now()
);

create table public.group_members (
  group_id uuid not null references public.groups (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  role text not null default 'member' check (role in ('owner', 'member')),
  joined_at timestamptz not null default now(),
  primary key (group_id, user_id)
);

create table public.categories (
  id uuid primary key default gen_random_uuid(),
  group_id uuid not null references public.groups (id) on delete cascade,
  name text not null,
  created_at timestamptz not null default now()
);

create table public.receipts (
  id uuid primary key default gen_random_uuid(),
  group_id uuid not null references public.groups (id) on delete cascade,
  uploaded_by uuid not null references auth.users (id) on delete cascade,
  category_id uuid references public.categories (id) on delete set null,
  merchant text,
  total_amount numeric(10, 2),
  currency text not null default 'USD',
  receipt_date date,
  image_path text,
  created_at timestamptz not null default now()
);

create table public.line_items (
  id uuid primary key default gen_random_uuid(),
  receipt_id uuid not null references public.receipts (id) on delete cascade,
  description text not null,
  quantity numeric(10, 2) not null default 1,
  unit_price numeric(10, 2) not null,
  total_price numeric(10, 2) not null,
  created_at timestamptz not null default now()
);

create table public.item_assignments (
  id uuid primary key default gen_random_uuid(),
  line_item_id uuid not null references public.line_items (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  share numeric(6, 4) not null default 1.0,
  created_at timestamptz not null default now(),
  unique (line_item_id, user_id)
);

create index on public.group_members (user_id);
create index on public.categories (group_id);
create index on public.receipts (group_id);
create index on public.line_items (receipt_id);
create index on public.item_assignments (line_item_id);
create index on public.item_assignments (user_id);

-- Row Level Security: membership-scoped access

alter table public.groups enable row level security;
alter table public.group_members enable row level security;
alter table public.categories enable row level security;
alter table public.receipts enable row level security;
alter table public.line_items enable row level security;
alter table public.item_assignments enable row level security;

create or replace function public.is_group_member(target_group_id uuid)
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists (
    select 1 from public.group_members
    where group_id = target_group_id and user_id = auth.uid()
  );
$$;

create policy "members can view their groups"
  on public.groups for select
  using (public.is_group_member(id));

create policy "authenticated users can create groups"
  on public.groups for insert
  with check (auth.uid() = created_by);

create policy "members can view group membership"
  on public.group_members for select
  using (public.is_group_member(group_id));

create policy "owners can manage membership"
  on public.group_members for insert
  with check (public.is_group_member(group_id));

create policy "members can view categories"
  on public.categories for select
  using (public.is_group_member(group_id));

create policy "members can manage categories"
  on public.categories for insert
  with check (public.is_group_member(group_id));

create policy "members can view receipts"
  on public.receipts for select
  using (public.is_group_member(group_id));

create policy "members can create receipts"
  on public.receipts for insert
  with check (public.is_group_member(group_id) and auth.uid() = uploaded_by);

create policy "members can view line items"
  on public.line_items for select
  using (
    exists (
      select 1 from public.receipts
      where receipts.id = line_items.receipt_id
        and public.is_group_member(receipts.group_id)
    )
  );

create policy "members can manage line items"
  on public.line_items for insert
  with check (
    exists (
      select 1 from public.receipts
      where receipts.id = line_items.receipt_id
        and public.is_group_member(receipts.group_id)
    )
  );

create policy "members can view item assignments"
  on public.item_assignments for select
  using (
    exists (
      select 1 from public.line_items
      join public.receipts on receipts.id = line_items.receipt_id
      where line_items.id = item_assignments.line_item_id
        and public.is_group_member(receipts.group_id)
    )
  );

create policy "members can manage item assignments"
  on public.item_assignments for insert
  with check (
    exists (
      select 1 from public.line_items
      join public.receipts on receipts.id = line_items.receipt_id
      where line_items.id = item_assignments.line_item_id
        and public.is_group_member(receipts.group_id)
    )
  );

-- Private storage bucket for receipt images
insert into storage.buckets (id, name, public)
values ('receipts', 'receipts', false)
on conflict (id) do nothing;

create policy "members can read their group's receipt images"
  on storage.objects for select
  using (
    bucket_id = 'receipts'
    and public.is_group_member((storage.foldername(name))[1]::uuid)
  );

create policy "members can upload their group's receipt images"
  on storage.objects for insert
  with check (
    bucket_id = 'receipts'
    and public.is_group_member((storage.foldername(name))[1]::uuid)
  );
