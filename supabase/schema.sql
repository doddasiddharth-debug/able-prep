-- Run once in the Supabase SQL editor. One row per user; the row holds the
-- same JSON the app keeps in localStorage. Row-level security limits every
-- user to their own row, which is what makes the anon key safe to publish.

create table if not exists public.progress (
  user_id    uuid primary key references auth.users (id) on delete cascade,
  state      jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

alter table public.progress enable row level security;

create policy "own row: read"   on public.progress for select using (auth.uid() = user_id);
create policy "own row: insert" on public.progress for insert with check (auth.uid() = user_id);
create policy "own row: update" on public.progress for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own row: delete" on public.progress for delete using (auth.uid() = user_id);

-- A progress row is small (a few hundred KB at most after a year of practice),
-- but cap it so a bug can't fill the database.
alter table public.progress add constraint state_size check (pg_column_size(state) < 4000000);
