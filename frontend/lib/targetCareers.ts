/**
 * Must match ml_pipeline/config.py TARGET_CAREERS order and strings exactly.
 * Update both if the label set changes.
 */
export const TARGET_CAREERS = [
  "Engineering",
  "Computer Science & Technology",
  "Business & Management",
  "Accounting & Finance",
  "Nursing & Allied Health",
  "Medicine (Pre-Med & Medical Fields)",
  "Education / Teaching",
  "Psychology & Behavioral Science",
  "Communication & Media",
  "Law & Legal Studies",
  "Architecture & Built Environment",
  "Agriculture & Environmental Studies",
  "Natural Sciences",
  "Arts & Design",
] as const;

export type TargetCareer = (typeof TARGET_CAREERS)[number];

export function isTargetCareer(s: string): s is TargetCareer {
  return (TARGET_CAREERS as readonly string[]).includes(s);
}
