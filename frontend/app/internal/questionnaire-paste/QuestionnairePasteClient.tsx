"use client";

import { useState, useEffect, useCallback, type FormEvent } from "react";
import { useRouter } from "next/navigation";

/** Matches unlock gate — dev-only; not a security boundary for sensitive data. */
const INTERNAL_PASTE_PIN = "testing";
const SESSION_UNLOCK_KEY = "internal_questionnaire_paste_unlocked";

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
    async (finalAnswers: number[]) => {
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

        const data = await response.json();
        localStorage.removeItem("questionnaire_progress");
        router.push(
          `/results?predictions=${encodeURIComponent(JSON.stringify(data.predictions))}`
        );
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

    if (lines.length !== questionnaire.total_questions) {
      alert(
        `Please provide exactly ${questionnaire.total_questions} non-empty lines. You provided ${lines.length}.`
      );
      return;
    }

    try {
      const presetAnswers: number[] = questionnaire.questions.map(
        (q: QuestionnaireQuestion, idx: number) => {
          const desired = lines[idx];
          let optionIndex = q.options.indexOf(desired);
          if (optionIndex === -1) {
            const lowerDesired = desired.toLowerCase();
            optionIndex = q.options.findIndex((opt: string) => opt.toLowerCase() === lowerDesired);
          }
          if (optionIndex === -1) {
            throw new Error(
              `Could not find an option matching your answer for question ${q.id}:\n"${desired}"`
            );
          }
          return optionIndex;
        }
      );
      handleSubmit(presetAnswers);
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
            Paste answers in order from question 1 to {questionnaire.total_questions}. Each line must
            match an option for that question (same text as in questionnaire.json).
          </p>
          <textarea
            value={pastedAnswers}
            onChange={(e) => setPastedAnswers(e.target.value)}
            className="w-full h-48 text-sm border border-gray-200 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 resize-y"
            placeholder={`Line 1: answer to question 1\nLine 2: answer to question 2\n...\nLine ${questionnaire.total_questions}: last answer`}
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
