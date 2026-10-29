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
