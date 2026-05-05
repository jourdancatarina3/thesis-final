-- Adds fields when participant answers no/not sure to top-3 fit:
-- actual career (one of 14 labels) + 1–5 ratings for each predicted top-3 field.

alter table public.employee_validation_sessions
  add column if not exists actual_career_field text,
  add column if not exists rating_top1 int,
  add column if not exists rating_top2 int,
  add column if not exists rating_top3 int;
