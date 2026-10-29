-- Run in the Supabase SQL editor
create table if not exists predictions (
  id uuid primary key,
  company_slug text not null,
  company_name text,
  industry text,
  hypothesis text not null,
  pattern_signature jsonb,
  confidence numeric,
  factors jsonb,
  created_at timestamptz not null default now(),
  status text not null default 'pending' check (status in ('pending','confirmed','refuted','expired')),
  resolved_at timestamptz,
  resolution_url text,
  resolution_note text
);
alter table predictions enable row level security;  -- no policies: only the service_role key can access

-- Watchlist + alert log (run in the Supabase SQL editor)
create table if not exists watchlist (
  id uuid primary key,
  company_slug text not null unique,
  company_name text not null,
  conf_move numeric default 10,
  min_weight numeric default 0.7,
  active boolean default true,
  created_at timestamptz not null default now()
);
create table if not exists alert_log (
  id uuid primary key,
  company_slug text not null,
  dedupe_key text not null unique,
  channels jsonb,
  created_at timestamptz not null default now()
);
alter table watchlist enable row level security;   -- no policies: service_role only
alter table alert_log enable row level security;
