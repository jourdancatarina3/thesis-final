export const STUDY_SESSION_STORAGE_KEY = "study_validation_v1";
export const CONSENT_VERSION = "2026-04-24";

export type FieldInTop3Answer = "yes" | "no" | "not_sure";

/** Fixed tenure buckets shown in screening (Step 2). */
export const TENURE_BAND_IDS = ["lt_1y", "y2", "y3", "y4", "gt_5y"] as const;
export type TenureBandId = (typeof TENURE_BAND_IDS)[number];

export const TENURE_BAND_LABELS: Record<TenureBandId, string> = {
  lt_1y: "Less than a year",
  y2: "2 years",
  y3: "3 years",
  y4: "4 years",
  gt_5y: "More than 5 years",
};

export function isTenureBandId(value: string): value is TenureBandId {
  return (TENURE_BAND_IDS as readonly string[]).includes(value);
}

/** Representative y/m/total months for CSV continuity (band midpoints). */
const TENURE_TO_PARTS: Record<
  TenureBandId,
  { tenureYears: number; tenureMonths: number; totalMonthsTenure: number }
> = {
  lt_1y: { tenureYears: 0, tenureMonths: 6, totalMonthsTenure: 6 },
  y2: { tenureYears: 2, tenureMonths: 0, totalMonthsTenure: 24 },
  y3: { tenureYears: 3, tenureMonths: 0, totalMonthsTenure: 36 },
  y4: { tenureYears: 4, tenureMonths: 0, totalMonthsTenure: 48 },
  gt_5y: { tenureYears: 6, tenureMonths: 0, totalMonthsTenure: 72 },
};

export function tenureBandToParts(band: TenureBandId): {
  tenureYears: number;
  tenureMonths: number;
  totalMonthsTenure: number;
} {
  return TENURE_TO_PARTS[band];
}

export interface QuestionnaireResponseItem {
  questionId: number;
  answerIndex: number;
}

export interface PredictionItem {
  career: string;
  probability: number;
}

export interface StudyScreening {
  participantName: string;
  tenureBand: TenureBandId;
  jobSatisfaction: 1 | 2 | 3 | 4 | 5;
}

export interface StudySession {
  sessionId: string;
  consentAccepted: boolean;
  consentTimestamp: string;
  consentVersion: string;
  screening?: StudyScreening;
  questionnaireResponses?: QuestionnaireResponseItem[];
  predictions?: PredictionItem[];
  questionnaireSubmittedAt?: string;
  fieldInTop3?: FieldInTop3Answer;
  ratingTop1?: number;
  ratingTop2?: number;
  ratingTop3?: number;
  feedbackSubmittedAt?: string;
}

function safeParse(raw: string | null): StudySession | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StudySession;
  } catch {
    return null;
  }
}

export function readStudySession(): StudySession | null {
  if (typeof window === "undefined") return null;
  return safeParse(sessionStorage.getItem(STUDY_SESSION_STORAGE_KEY));
}

export function writeStudySession(session: StudySession): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(STUDY_SESSION_STORAGE_KEY, JSON.stringify(session));
}

export function patchStudySession(partial: Partial<StudySession>): StudySession | null {
  const cur = readStudySession();
  if (!cur) return null;
  const next = { ...cur, ...partial };
  writeStudySession(next);
  return next;
}

export function createEmptyStudySession(): StudySession {
  return {
    sessionId: crypto.randomUUID(),
    consentAccepted: false,
    consentTimestamp: "",
    consentVersion: CONSENT_VERSION,
  };
}

export function ensureStudySession(): StudySession {
  const existing = readStudySession();
  if (existing?.sessionId) return existing;
  const fresh = createEmptyStudySession();
  writeStudySession(fresh);
  return fresh;
}

export function validateScreening(s: StudyScreening): string | null {
  if (!isTenureBandId(s.tenureBand)) return "Please select how long you have been in your current job or role.";
  if (s.jobSatisfaction < 1 || s.jobSatisfaction > 5) return "Please rate your job satisfaction.";
  return null;
}
