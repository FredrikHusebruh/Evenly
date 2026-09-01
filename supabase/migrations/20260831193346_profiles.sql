-- profiles: denormalized (email, optional username) per auth user, joined in
-- app code (no direct FK exists between group_members/profiles to embed via
-- PostgREST, and neither table would gain one just for this).

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null,
  username text,
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create or replace function public.shares_group_with(target_user_id uuid)
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists (
    select 1
    from public.group_members gm1
    join public.group_members gm2 on gm1.group_id = gm2.group_id
    where gm1.user_id = auth.uid() and gm2.user_id = target_user_id
  );
$$;

create policy "self or groupmates can view profile"
  on public.profiles for select
  using (id = auth.uid() or public.shares_group_with(id));

create policy "self can update own profile"
  on public.profiles for update
  using (id = auth.uid())
  with check (id = auth.uid());

-- Column-level lockdown: the RLS UPDATE policy above is row-scoped only, so
-- without this a user could PATCH their own `email` directly against
-- PostgREST (bypassing the backend entirely, using nothing but the anon key
-- + session token they already hold) — email is system-maintained via the
-- triggers below, never client-writable.
revoke update on public.profiles from authenticated;
grant update (username) on public.profiles to authenticated;

-- No insert/delete policy for `authenticated`: rows are created only by the
-- trigger below (or the one-time backfill), and deletion cascades from
-- auth.users. Not a signup-gated privilege grant (see security.md's "never
-- grant privileges from a signup trigger" rule) — this only ever creates a
-- row scoped to the signing-up user's own id/email, granting no membership,
-- role, or invitation to anyone.

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

create or replace function public.handle_user_email_updated()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if new.email is distinct from old.email then
    update public.profiles set email = new.email where id = new.id;
  end if;
  return new;
end;
$$;

create trigger on_auth_user_email_updated
  after update of email on auth.users
  for each row execute function public.handle_user_email_updated();

-- Backfill: users created before this migration have no profile row yet.
insert into public.profiles (id, email)
select id, email from auth.users
on conflict (id) do nothing;
