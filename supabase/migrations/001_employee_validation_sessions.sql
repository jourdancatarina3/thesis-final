-- Validation study submissions (POST /api/study-response from Next.js).
-- Run in Supabase SQL Editor once, or via Supabase CLI migrations.

create table if not exists public.employee_validation_sessions (
  id uuid primary key default gen_random_uuid(),
  session_id text not null,
  consent_version text not null default '',
  participant_name text not null,
  tenure_band text not null,
  tenure_total_months int not null,
  tenure_years_part int not null,
  tenure_months_part int not null,
  job_satisfaction int not null,
  responses_json jsonb not null,
  pred_career_1 text not null default '',
  pred_prob_1 double precision,
  pred_career_2 text not null default '',
  pred_prob_2 double precision,
  pred_career_3 text not null default '',
  pred_prob_3 double precision,
  computed_self_reported_in_top3 boolean not null default false,
  participant_field_in_top3_answer text not null,
  constraint employee_validation_sessions_session_id_key unique (session_id)
);

comment on table public.employee_validation_sessions is
  'Thesis employee validation study: one row per completed session (service role insert from Vercel).';

alter table public.employee_validation_sessions enable row level security;
