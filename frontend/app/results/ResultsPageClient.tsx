"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import ResultsCard from "@/components/ResultsCard";
import LoadingSpinner from "@/components/LoadingSpinner";
import Link from "next/link";
import { CAREER_DESCRIPTIONS } from "@/lib/careerDescriptions";
import {
  patchStudySession,
  readStudySession,
  STUDY_SESSION_STORAGE_KEY,
  type FieldInTop3Answer,
  type PredictionItem,
} from "@/lib/studySession";

interface Prediction {
  career: string;
  probability: number;
  traits?: string[];
  description?: string;
}

export default function ResultsPageClient() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [studyMode, setStudyMode] = useState(false);

  const [fieldInTop3, setFieldInTop3] = useState<FieldInTop3Answer | "">("");
  const [rating1, setRating1] = useState<number>(0);
  const [rating2, setRating2] = useState<number>(0);
  const [rating3, setRating3] = useState<number>(0);
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [thankYou, setThankYou] = useState(false);
  const [alreadySubmitted, setAlreadySubmitted] = useState(false);

  useEffect(() => {
    const predictionsParam = searchParams.get("predictions");
    const session = readStudySession();

    if (session?.feedbackSubmittedAt) {
      setAlreadySubmitted(true);
      setThankYou(true);
      if (session.predictions?.length) {
        const top3 = session.predictions.slice(0, 3).map((p: PredictionItem) => ({
          ...p,
          description: CAREER_DESCRIPTIONS[p.career] || "",
        }));
        setPredictions(top3);
      }
      setLoading(false);
      return;
    }

    let parsed: PredictionItem[] | null = null;
    const fromUrl = Boolean(predictionsParam);

    if (predictionsParam) {
      try {
        parsed = JSON.parse(decodeURIComponent(predictionsParam));
      } catch (e) {
        console.error("Failed to parse predictions", e);
        router.push("/");
        return;
      }
    } else if (session?.predictions && session.predictions.length >= 3) {
      parsed = session.predictions;
    }

    if (!parsed || !Array.isArray(parsed) || parsed.length < 3) {
      router.push("/");
      return;
    }

    const top3 = parsed.slice(0, 3).map((p: PredictionItem) => ({
      ...p,
      description: CAREER_DESCRIPTIONS[p.career] || "",
    }));
    setPredictions(top3);

    const isStudy =
      !fromUrl &&
      Boolean(
        session?.screening &&
          session.questionnaireResponses?.length === 30 &&
          session.predictions
      );
    setStudyMode(isStudy);

    setLoading(false);
  }, [searchParams, router]);

  const showRatingBlock = fieldInTop3 === "no" || fieldInTop3 === "not_sure";

  const canSubmitFeedback = useMemo(() => {
    if (!studyMode || thankYou) return false;
    if (!fieldInTop3) return false;
    if (fieldInTop3 === "yes") return true;
    return rating1 >= 1 && rating1 <= 5 && rating2 >= 1 && rating2 <= 5 && rating3 >= 1 && rating3 <= 5;
  }, [studyMode, thankYou, fieldInTop3, rating1, rating2, rating3]);

  const handleFeedbackSubmit = useCallback(async () => {
    if (!canSubmitFeedback || !fieldInTop3) return;
    const session = readStudySession();
    if (!session?.screening || !session.questionnaireResponses || !session.predictions) return;

    setSubmittingFeedback(true);
    const payload = {
      sessionId: session.sessionId,
      consentVersion: session.consentVersion,
      consentTimestamp: session.consentTimestamp,
      screening: session.screening,
      questionnaireResponses: session.questionnaireResponses,
      predictions: session.predictions,
      fieldInTop3,
      computedSelfReportedInTop3: false,
      feedbackSubmittedAt: new Date().toISOString(),
      ...(showRatingBlock
        ? { ratingTop1: rating1, ratingTop2: rating2, ratingTop3: rating3 }
        : {}),
    };

    try {
      const res = await fetch("/api/study-response", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as { error?: string }).error || "Save failed");
      }
      patchStudySession({
        fieldInTop3,
        ratingTop1: showRatingBlock ? rating1 : undefined,
        ratingTop2: showRatingBlock ? rating2 : undefined,
        ratingTop3: showRatingBlock ? rating3 : undefined,
        feedbackSubmittedAt: payload.feedbackSubmittedAt,
      });
      setThankYou(true);
    } catch (e) {
      console.error(e);
      alert(e instanceof Error ? e.message : "Could not save your responses. Please try again.");
    } finally {
      setSubmittingFeedback(false);
    }
  }, [
    canSubmitFeedback,
    fieldInTop3,
    showRatingBlock,
    rating1,
    rating2,
    rating3,
  ]);

  if (loading) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (thankYou && alreadySubmitted && predictions.length === 0) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center px-4">
        <div className="max-w-md text-center bg-white rounded-xl shadow-md p-8 border border-gray-200">
          <p className="text-gray-800 font-semibold mb-2">Response already recorded</p>
          <p className="text-sm text-gray-600 mb-6">Thank you for participating in this study.</p>
          <Link href="/" className="text-indigo-600 font-semibold hover:underline">
            Back to home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 py-6 px-4 sm:py-12">
      <div className="max-w-5xl mx-auto">
        {thankYou ? (
          <div className="text-center mb-8 max-w-xl mx-auto bg-white rounded-xl shadow-md p-6 border border-emerald-100 sm:mb-12 sm:p-10">
            <div className="inline-block p-3 bg-emerald-100 rounded-full mb-4">
              <svg className="w-8 h-8 sm:w-10 sm:h-10 text-emerald-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-gray-900 mb-2 sm:text-2xl">Thank you</h1>
            <p className="text-gray-600 mb-6">
              Your answers have been saved for the research study. You may close this window.
            </p>
            <button
              type="button"
              onClick={() => {
                sessionStorage.removeItem(STUDY_SESSION_STORAGE_KEY);
                router.push("/");
              }}
              className="px-6 py-3 rounded-xl bg-slate-800 text-white font-semibold hover:bg-slate-900"
            >
              Back to home
            </button>
          </div>
        ) : (
          <>
            <div className="text-center mb-8 sm:mb-12">
              <div className="inline-block p-3 sm:p-4 bg-slate-100 rounded-full mb-3 sm:mb-4">
                <svg className="w-10 h-10 sm:w-12 sm:h-12 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2 sm:text-3xl md:text-4xl">
                Your college field recommendations
              </h1>
              <p className="text-base text-gray-600 max-w-xl mx-auto sm:text-lg">
                Based on your responses, here are three college fields that match your profile.
              </p>
              <p className="text-sm text-gray-500 mt-2 italic">Listed in no particular order</p>
            </div>

            <div className="space-y-4 mb-8 sm:space-y-5 sm:mb-12">
              {predictions.map((prediction, index) => (
                <ResultsCard
                  key={prediction.career + String(index)}
                  career={prediction.career}
                  description={prediction.description}
                  accentColor={["slate", "teal", "amber"][index] as "slate" | "teal" | "amber"}
                />
              ))}
            </div>

            {studyMode && !thankYou && (
              <div className="bg-white rounded-xl shadow-md p-5 md:p-8 border border-indigo-100 mb-6 sm:mb-8">
                <h2 className="text-lg font-bold text-gray-900 mb-2 sm:text-xl">Quick validation</h2>
                <p className="text-sm text-gray-600 mb-6">
                  Your answers help assess how well these recommendations align with people already working
                  in each career field.
                </p>

                <div className="mb-6">
                  <p className="text-sm font-semibold text-gray-800 mb-3">
                    Is your current job or career field represented among these three recommendations?
                  </p>
                  <div className="flex flex-col sm:flex-row gap-2">
                    {(
                      [
                        ["yes", "Yes"],
                        ["no", "No"],
                        ["not_sure", "Not sure"],
                      ] as const
                    ).map(([val, label]) => (
                      <label
                        key={val}
                        className={`flex-1 cursor-pointer rounded-lg border-2 px-4 py-3 text-center text-sm font-medium transition-all ${
                          fieldInTop3 === val
                            ? "border-indigo-600 bg-indigo-50 text-indigo-900"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        <input
                          type="radio"
                          name="fit"
                          className="sr-only"
                          checked={fieldInTop3 === val}
                          onChange={() => setFieldInTop3(val)}
                        />
                        {label}
                      </label>
                    ))}
                  </div>
                </div>

                {showRatingBlock && (
                  <div className="space-y-6 mb-6 border-t border-gray-100 pt-6">
                    <p className="text-sm text-gray-700">
                      For each recommendation below, how close is it to college fields or career directions you
                      would personally consider? (1 = not at all, 5 = very close)
                    </p>
                    {predictions.slice(0, 3).map((p, i) => {
                      const setR = i === 0 ? setRating1 : i === 1 ? setRating2 : setRating3;
                      const r = i === 0 ? rating1 : i === 1 ? rating2 : rating3;
                      return (
                        <div key={p.career} className="rounded-lg border border-gray-100 p-4 bg-gray-50/80">
                          <p className="text-sm font-semibold text-gray-900 mb-2">{p.career}</p>
                          <div className="flex flex-wrap gap-2">
                            {[1, 2, 3, 4, 5].map((n) => (
                              <button
                                key={n}
                                type="button"
                                onClick={() => setR(n)}
                                className={`min-w-[2.5rem] py-2 rounded-lg text-sm font-medium border-2 transition-all ${
                                  r === n
                                    ? "border-indigo-600 bg-indigo-600 text-white"
                                    : "border-gray-200 bg-white text-gray-700 hover:border-gray-300"
                                }`}
                              >
                                {n}
                              </button>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                <button
                  type="button"
                  disabled={!canSubmitFeedback || submittingFeedback}
                  onClick={handleFeedbackSubmit}
                  className={`w-full sm:w-auto px-8 py-3 rounded-xl font-semibold transition-all ${
                    canSubmitFeedback && !submittingFeedback
                      ? "bg-indigo-600 text-white hover:bg-indigo-700 shadow-md"
                      : "bg-gray-200 text-gray-400 cursor-not-allowed"
                  }`}
                >
                  {submittingFeedback ? "Saving…" : "Submit and finish"}
                </button>
              </div>
            )}

            <div className="bg-white rounded-xl shadow-md p-5 md:p-12 text-center border border-gray-200 sm:p-8">
              <h2 className="text-xl font-bold text-gray-800 mb-3 sm:text-2xl sm:mb-4">Next steps</h2>
              <p className="text-gray-600 mb-6 text-base leading-relaxed max-w-2xl mx-auto sm:mb-8 sm:text-lg">
                {studyMode
                  ? "If you need to start over with a new session, use the button below. Your completed response has been or will be saved when you submit the validation section above."
                  : "Consider exploring these college fields further. Research each option and speak with people in these areas to see what fits your goals."}
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  href={studyMode ? "/study?restart=1" : "/questionnaire"}
                  className="px-6 py-3 text-sm bg-gray-600 text-white rounded-xl hover:bg-gray-700 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 sm:px-8 sm:py-4 sm:text-base"
                >
                  {studyMode ? "Start a new study session" : "Retake questionnaire"}
                </Link>
                <Link
                  href="/"
                  className="px-6 py-3 text-sm bg-slate-700 text-white rounded-xl hover:bg-slate-800 transition-all duration-200 font-semibold shadow-md hover:shadow-lg sm:px-8 sm:py-4 sm:text-base"
                >
                  Back to home
                </Link>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
