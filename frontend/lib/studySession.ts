import type { TargetCareer } from "./targetCareers";
import { TARGET_CAREERS } from "./targetCareers";

export const STUDY_SESSION_STORAGE_KEY = "study_validation_v1";
export const CONSENT_VERSION = "2026-04-24";

export type FieldInTop3Answer = "yes" | "no" | "not_sure";

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
  tenureYears: number;
  tenureMonths: number;
  totalMonthsTenure: number;
  jobSatisfaction: 1 | 2 | 3 | 4 | 5;
  selfReportedCareerField: TargetCareer;
  jobTitle: string;
  totalWorkExperienceYears: string;
  educationLevel: string;
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

/** Exact career label match against top-3 model outputs. */
export function computeSelfReportedFieldInTop3(
  selfReported: string,
  predictions: PredictionItem[]
): boolean {
  const top = predictions.slice(0, 3).map((p) => p.career.trim());
  return top.includes(selfReported.trim());
}

export function validateScreening(s: StudyScreening): string | null {
  if (!s.participantName.trim()) return "Please enter your name.";
  if (s.totalMonthsTenure <= 0) return "Please enter how long you have been in your current job (years and/or months).";
  if (s.jobSatisfaction < 1 || s.jobSatisfaction > 5) return "Please rate your job satisfaction.";
  if (!TARGET_CAREERS.includes(s.selfReportedCareerField as TargetCareer))
    return "Please select your current career field.";
  return null;
}
