-- Memolex : signalements de cartes (drapeau « Signaler une erreur »). À lancer une fois dans Supabase → SQL Editor (projet memolex),
-- APRÈS avoir déployé la fonction memolex-report. Remplacer REPORT_SECRET_ICI par la valeur du secret REPORT_SECRET de la fonction.
create table if not exists public.memolex_report (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  user_id uuid default auth.uid() references auth.users(id) on delete set null,
  lang text not null check (lang in ('de','it')),
  reason text not null check (reason in ('trad','exemple','chunk','gram','offensif','autre')),
  comment text not null default '' check (char_length(comment) <= 1000),
  card jsonb not null check (pg_column_size(card) < 12000),
  app_ver text check (char_length(app_ver) <= 20),
  client_id text check (char_length(client_id) <= 64),
  status text not null default 'nouveau',   -- nouveau · analysé · corrigé · rejeté
  gh_issue int
);
alter table public.memolex_report enable row level security;
-- les utilisateurs peuvent seulement AJOUTER un signalement (connectés ou non) ; personne ne peut les lire depuis l'appli
drop policy if exists "report insert" on public.memolex_report;
create policy "report insert" on public.memolex_report for insert to anon, authenticated
  with check (user_id is null or user_id = auth.uid());
revoke all on public.memolex_report from anon, authenticated;
grant insert (lang, reason, comment, card, app_ver, client_id) on public.memolex_report to anon, authenticated;

-- garde-fou contre l'abus : 30 signalements par heure et par appareil, 300 par heure au total
create or replace function public.memolex_report_guard() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if (select count(*) from public.memolex_report where created_at > now() - interval '1 hour') >= 300
     or (select count(*) from public.memolex_report where client_id = new.client_id and created_at > now() - interval '1 hour') >= 30 then
    raise exception 'trop de signalements, réessaie plus tard' using errcode = 'P0001';
  end if;
  return new;
end $$;
drop trigger if exists memolex_report_guard on public.memolex_report;
create trigger memolex_report_guard before insert on public.memolex_report for each row execute function public.memolex_report_guard();

-- chaque nouveau signalement est transmis à la fonction memolex-report, qui ouvre une issue GitHub
create extension if not exists pg_net;
create or replace function public.memolex_report_notify() returns trigger language plpgsql security definer set search_path = public as $$
begin
  perform net.http_post(
    url := 'https://rbgxotiadewxlyvvrdhp.supabase.co/functions/v1/memolex-report',
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-report-secret', 'REPORT_SECRET_ICI'),
    body := jsonb_build_object('id', new.id),
    timeout_milliseconds := 15000);
  return new;
end $$;
drop trigger if exists memolex_report_notify on public.memolex_report;
create trigger memolex_report_notify after insert on public.memolex_report for each row execute function public.memolex_report_notify();

-- relire les signalements :  select id, created_at, lang, reason, card->>'de' as mot, card->>'fr' as fr, comment, status, gh_issue
--                            from public.memolex_report order by id desc limit 50;
-- renvoyer vers GitHub ceux qui n'ont pas d'issue (après une panne) :
--   select net.http_post(url := 'https://rbgxotiadewxlyvvrdhp.supabase.co/functions/v1/memolex-report',
--     headers := jsonb_build_object('Content-Type','application/json','x-report-secret','REPORT_SECRET_ICI'),
--     body := jsonb_build_object('id', id)) from public.memolex_report where gh_issue is null;
