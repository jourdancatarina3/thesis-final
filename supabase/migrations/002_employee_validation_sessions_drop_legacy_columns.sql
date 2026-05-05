-- Apply if you already ran the previous version of 001 (extra columns / timestamps).
-- Safe to run once on existing databases; no-op if columns were never created.

drop index if exists idx_employee_validation_sessions_created_at;

alter table public.employee_validation_sessions
  drop column if exists created_at,
  drop column if exists submitted_at_utc,
  drop column if exists consent_timestamp,
  drop column if exists self_reported_career_field,
  drop column if exists job_title,
  drop column if exists total_work_experience_years,
  drop column if exists education_level,
  drop column if exists rating_top1,
  drop column if exists rating_top2,
  drop column if exists rating_top3;
