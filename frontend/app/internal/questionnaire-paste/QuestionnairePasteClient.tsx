"use client";

import { useState, useEffect, useCallback, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import {
  CONSENT_VERSION,
  TENURE_BAND_IDS,
  TENURE_BAND_LABELS,
  isTenureBandId,
  validateScreening,
  writeStudySession,
  type TenureBandId,
  type StudyScreening,
} from "@/lib/studySession";

/** Matches unlock gate — dev-only; not a security boundary for sensitive data. */
const INTERNAL_PASTE_PIN = "testing";
const SESSION_UNLOCK_KEY = "internal_questionnaire_paste_unlocked";

/** First lines: tenure in role, job satisfaction — same as /study screening (required). */
const PASTE_HEADER_LINE_COUNT = 2;

const SATISFACTION_LABEL_TO_VALUE: Record<string, 1 | 2 | 3 | 4 | 5> = {
  "1": 1,
  "2": 2,
  "3": 3,
  "4": 4,
  "5": 5,
  "very dissatisfied": 1,
  dissatisfied: 2,
  neutral: 3,
  satisfied: 4,
  "very satisfied": 5,
};

function parseTenureLine(line: string): TenureBandId {
  const raw = line.trim();
  if (isTenureBandId(raw)) return raw;
  const lower = raw.toLowerCase();
  for (const id of TENURE_BAND_IDS) {
    if (TENURE_BAND_LABELS[id].toLowerCase() === lower) return id;
  }
  const options = TENURE_BAND_IDS.map((id) => `${TENURE_BAND_LABELS[id]} (${id})`).join("; ");
  throw new Error(
    `Line 1 (time in current role): no match for "${raw}". Use one of: ${options}`
  );
}

function parseSatisfactionLine(line: string): 1 | 2 | 3 | 4 | 5 {
  const raw = line.trim();
  const direct = SATISFACTION_LABEL_TO_VALUE[raw.toLowerCase()];
  if (direct !== undefined) return direct;
  const n = Number.parseInt(raw, 10);
  if (!Number.isNaN(n) && n >= 1 && n <= 5 && String(n) === raw.trim()) {
    return n as 1 | 2 | 3 | 4 | 5;
  }
  throw new Error(
    `Line 2 (job satisfaction): use 1–5 or: Very dissatisfied, Dissatisfied, Neutral, Satisfied, Very satisfied`
  );
}

/** So pasted text still matches when copy sources use curly apostrophes, NBSP, or extra spaces. */
function normalizeOptionLine(s: string): string {
  return s
    .trim()
    .replace(/\u00a0/g, " ")
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201c\u201d]/g, '"')
    .replace(/\s+/g, " ");
}

interface QuestionnaireQuestion {
  id: number;
  category: string;
  question: string;
  options: string[];
}

interface QuestionnaireData {
  title: string;
  description: string;
  total_questions: number;
  questions: QuestionnaireQuestion[];
}

export default function QuestionnairePasteClient() {
  const router = useRouter();
  const [unlocked, setUnlocked] = useState(false);
  const [pinInput, setPinInput] = useState("");
  const [pinError, setPinError] = useState(false);
  const [questionnaire, setQuestionnaire] = useState<QuestionnaireData | null>(null);
  const [pastedAnswers, setPastedAnswers] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (sessionStorage.getItem(SESSION_UNLOCK_KEY) === "1") {
      setUnlocked(true);
    }
  }, []);

  useEffect(() => {
    if (!unlocked) return;
    fetch("/questionnaire.json")
      .then((res) => res.json())
      .then((data: QuestionnaireData) => setQuestionnaire(data))
      .catch((err) => {
        console.error("Failed to load questionnaire:", err);
        alert("Failed to load questionnaire. Please refresh the page.");
      });
  }, [unlocked]);

  const handleUnlock = (e: FormEvent) => {
    e.preventDefault();
    if (pinInput === INTERNAL_PASTE_PIN) {
      sessionStorage.setItem(SESSION_UNLOCK_KEY, "1");
      setPinError(false);
      setUnlocked(true);
      setPinInput("");
    } else {
      setPinError(true);
    }
  };

  const handleSubmit = useCallback(
    async (finalAnswers: number[], screening: StudyScreening) => {
      if (!questionnaire) return;

      setIsSubmitting(true);
      try {
        const responses = questionnaire.questions.map((q: QuestionnaireQuestion, idx: number) => ({
          questionId: q.id,
          answerIndex: finalAnswers[idx],
        }));

        const response = await fetch("/api/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ responses }),
        });

        if (!response.ok) throw new Error("Failed to get predictions");

        const data = (await response.json()) as { predictions: { career: string; probability: number }[] };
        localStorage.removeItem("questionnaire_progress");

        // Same shape as /study so /results shows “Quick validation” and /api/study-response can save.
        writeStudySession({
          sessionId: crypto.randomUUID(),
          consentAccepted: true,
          consentTimestamp: new Date().toISOString(),
          consentVersion: CONSENT_VERSION,
          screening,
          questionnaireResponses: responses,
          predictions: data.predictions,
          questionnaireSubmittedAt: new Date().toISOString(),
        });
        router.push("/results");
      } catch (error) {
        console.error("Error submitting questionnaire:", error);
        alert("An error occurred. Please try again.");
        setIsSubmitting(false);
      }
    },
    [questionnaire, router]
  );

  const handlePastedAnswersSubmit = useCallback(() => {
    if (!questionnaire) {
      alert("Questionnaire not loaded yet.");
      return;
    }

    const lines = pastedAnswers
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    const requiredLines = PASTE_HEADER_LINE_COUNT + questionnaire.total_questions;
    if (lines.length !== requiredLines) {
      alert(
        `Please provide exactly ${requiredLines} non-empty lines: line 1 = time in current role, line 2 = job satisfaction, then ${questionnaire.total_questions} questionnaire answers (one per line). You provided ${lines.length}.`
      );
      return;
    }

    let tenureBand: TenureBandId;
    let jobSatisfaction: 1 | 2 | 3 | 4 | 5;
    try {
      tenureBand = parseTenureLine(lines[0]);
      jobSatisfaction = parseSatisfactionLine(lines[1]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      alert(msg);
      return;
    }

    const screening: StudyScreening = {
      participantName: "",
      tenureBand,
      jobSatisfaction,
    };
    const screeningErr = validateScreening(screening);
    if (screeningErr) {
      alert(screeningErr);
      return;
    }

    const questionLines = lines.slice(PASTE_HEADER_LINE_COUNT);

    try {
      const presetAnswers: number[] = questionnaire.questions.map(
        (q: QuestionnaireQuestion, idx: number) => {
          const desiredRaw = questionLines[idx];
          const desiredNorm = normalizeOptionLine(desiredRaw);
          let optionIndex = q.options.findIndex((opt: string) => normalizeOptionLine(opt) === desiredNorm);
          if (optionIndex === -1) {
            const lowerDesired = desiredNorm.toLowerCase();
            optionIndex = q.options.findIndex(
              (opt: string) => normalizeOptionLine(opt).toLowerCase() === lowerDesired
            );
          }
          if (optionIndex === -1) {
            throw new Error(
              `Could not find an option matching your answer for question ${q.id}:\n"${desiredRaw.trim()}"`
            );
          }
          return optionIndex;
        }
      );
      handleSubmit(presetAnswers, screening);
    } catch (e: unknown) {
      console.error("Failed to submit pasted answers:", e);
      const msg =
        e instanceof Error ? e.message : "Failed to submit pasted answers. Please check them.";
      alert(msg);
    }
  }, [questionnaire, pastedAnswers, handleSubmit]);

  if (!unlocked) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center px-4">
        <form
          onSubmit={handleUnlock}
          className="w-full max-w-sm bg-white/95 rounded-xl shadow-xl p-8 border border-slate-200"
        >
          <h1 className="text-lg font-semibold text-slate-800 mb-1">Restricted</h1>
          <p className="text-sm text-slate-500 mb-6">Enter PIN to continue.</p>
          <label htmlFor="paste-pin" className="sr-only">
            PIN
          </label>
          <input
            id="paste-pin"
            type="password"
            autoComplete="off"
            value={pinInput}
            onChange={(e) => {
              setPinInput(e.target.value);
              setPinError(false);
            }}
            className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 mb-3 ${
              pinError
                ? "border-red-400 focus:ring-red-300"
                : "border-slate-300 focus:ring-slate-400"
            }`}
            placeholder="PIN"
          />
          {pinError && <p className="text-xs text-red-600 mb-3">Incorrect PIN.</p>}
          <button
            type="submit"
            className="w-full py-2.5 rounded-lg text-sm font-semibold bg-slate-800 text-white hover:bg-slate-900 transition-colors"
          >
            Unlock
          </button>
        </form>
      </div>
    );
  }

  if (!questionnaire) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute top-0 left-0 w-full h-full border-4 border-blue-200 rounded-full" />
            <div className="absolute top-0 left-0 w-full h-full border-4 border-blue-600 rounded-full border-t-transparent animate-spin" />
          </div>
          <p className="text-gray-600 text-lg">Loading questionnaire…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl shadow-md p-6 border border-dashed border-blue-200">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-700">Paste answers (one per line)</h2>
            <span className="text-[11px] uppercase tracking-wide text-blue-500 font-semibold">
              Internal test
            </span>
          </div>
          <p className="text-xs text-gray-500 mb-3">
            <span className="font-medium text-gray-600">Line 1:</span> time in your current role — same
            options as study screening (
            {TENURE_BAND_IDS.map((id) => TENURE_BAND_LABELS[id]).join(", ")}).{" "}
            <span className="font-medium text-gray-600">Line 2:</span> job satisfaction —{" "}
            <code className="text-[11px]">1</code>–<code className="text-[11px]">5</code> or Very
            dissatisfied / Dissatisfied / Neutral / Satisfied / Very satisfied.{" "}
            <span className="font-medium text-gray-600">Lines 3–{2 + questionnaire.total_questions}:</span>{" "}
            questionnaire answers in order (same wording as{" "}
            <code className="text-[11px]">questionnaire.json</code>; straight quotes). Curly apostrophes
            from copy/paste are accepted.
            results page includes the same validation survey as <code className="text-[11px]">/study</code>{" "}
            so you can record whether your field appears in the top three.
          </p>
          <textarea
            value={pastedAnswers}
            onChange={(e) => setPastedAnswers(e.target.value)}
            className="w-full h-48 text-sm border border-gray-200 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 resize-y"
            placeholder={`Line 1: Less than a year (or y2, y3, …)\nLine 2: 4  or  Satisfied\nLine 3: first MCQ option text\n…\nLine ${2 + questionnaire.total_questions}: last MCQ option`}
          />
          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={handlePastedAnswersSubmit}
              disabled={isSubmitting || !pastedAnswers.trim()}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${
                isSubmitting || !pastedAnswers.trim()
                  ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                  : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-md"
              }`}
            >
              {isSubmitting ? "Submitting…" : "Submit from pasted answers"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
