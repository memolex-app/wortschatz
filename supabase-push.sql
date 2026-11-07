-- Memolex : notifications (rappels et mot du jour). À lancer une fois dans Supabase → SQL Editor (projet memolex),
-- APRÈS avoir déployé la fonction memolex-push. Remplacer CRON_SECRET_ICI par la valeur du secret CRON_SECRET.
create table if not exists public.memolex_push (
  endpoint text primary key,
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  sub jsonb not null,
  sent jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
alter table public.memolex_push enable row level security;
drop policy if exists "own subs" on public.memolex_push;
create policy "own subs" on public.memolex_push for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());

create extension if not exists pg_cron;
create extension if not exists pg_net;
select cron.unschedule('memolex-push') where exists (select 1 from cron.job where jobname = 'memolex-push');
select cron.schedule('memolex-push', '*/15 * * * *', $$
  select net.http_post(
    url := 'https://rbgxotiadewxlyvvrdhp.supabase.co/functions/v1/memolex-push',
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-cron-secret', 'CRON_SECRET_ICI'),
    body := '{}'::jsonb,
    timeout_milliseconds := 20000
  );
$$);
