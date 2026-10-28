-- Memolex : table de synchronisation. À lancer une fois dans Supabase → SQL Editor (projet memolex).
create table if not exists public.memolex (
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  id text not null,
  data jsonb,
  deleted boolean not null default false,
  srv_at timestamptz not null default now(),
  primary key (user_id, id)
);
create index if not exists memolex_user_srv on public.memolex (user_id, srv_at);
alter table public.memolex enable row level security;
drop policy if exists "own rows" on public.memolex;
create policy "own rows" on public.memolex for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());
create or replace function public.memolex_touch() returns trigger language plpgsql as $$
begin new.srv_at := clock_timestamp(); return new; end $$;
drop trigger if exists memolex_touch on public.memolex;
create trigger memolex_touch before insert or update on public.memolex
  for each row execute function public.memolex_touch();
