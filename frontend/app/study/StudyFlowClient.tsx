"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import QuestionnaireClient from "@/app/questionnaire/QuestionnaireClient";
import {
  CONSENT_VERSION,
  ensureStudySession,
  isTenureBandId,
  readStudySession,
  TENURE_BAND_IDS,
  TENURE_BAND_LABELS,
  validateScreening,
  writeStudySession,
  type StudyScreening,
  type StudySession,
  type TenureBandId,
} from "@/lib/studySession";

type FlowStep = "consent" | "screening" | "questionnaire";

function inferStep(session: StudySession): FlowStep {
  if (!session.consentAccepted) return "consent";
  if (!session.screening) return "screening";
  if (!session.predictions?.length) return "questionnaire";
  return "questionnaire";
}

export default function StudyFlowClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [step, setStep] = useState<FlowStep>("consent");
  const [consentReadChecked, setConsentReadChecked] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  const [name, setName] = useState("");
  const [tenureBand, setTenureBand] = useState<TenureBandId | "">("");
  const [tenureMenuOpen, setTenureMenuOpen] = useState(false);
  const tenureDropdownRef = useRef<HTMLDivElement>(null);
  const [satisfaction, setSatisfaction] = useState<1 | 2 | 3 | 4 | 5 | 0>(0);
  const [sessionId, setSessionId] = useState("");

  const restart = searchParams.get("restart") === "1";

  useEffect(() => {
    if (!tenureMenuOpen) return;
    const onPointerDown = (e: PointerEvent) => {
      if (tenureDropdownRef.current?.contains(e.target as Node)) return;
      setTenureMenuOpen(false);
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setTenureMenuOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [tenureMenuOpen]);

  useEffect(() => {
    if (step !== "screening") setTenureMenuOpen(false);
  }, [step]);

  useEffect(() => {
    if (!restart) return;
    const fresh = {
      sessionId: crypto.randomUUID(),
      consentAccepted: false,
      consentTimestamp: "",
      consentVersion: CONSENT_VERSION,
    };
    writeStudySession(fresh);
    router.replace("/study");
  }, [restart, router]);

  useEffect(() => {
    if (restart) return;
    const session = ensureStudySession();
    setSessionId(session.sessionId);
    if (session.predictions?.length) {
      router.replace("/results");
      return;
    }
    setStep(inferStep(session));
    if (session.screening) {
      setName(session.screening.participantName);
      if (isTenureBandId(session.screening.tenureBand)) {
        setTenureBand(session.screening.tenureBand);
      }
      setSatisfaction(session.screening.jobSatisfaction);
    }
    setHydrated(true);
  }, [restart, router]);

  const stepIndex = step === "consent" ? 1 : step === "screening" ? 2 : 3;
  const stepLabel = "Step " + stepIndex + " of 4";

  const handleConsentContinue = () => {
    if (!consentReadChecked) return;
    const base = readStudySession() ?? ensureStudySession();
    const next: StudySession = {
      ...base,
      consentAccepted: true,
      consentTimestamp: new Date().toISOString(),
      consentVersion: CONSENT_VERSION,
    };
    writeStudySession(next);
    setStep("screening");
  };

  const handleScreeningContinue = () => {
    if (!isTenureBandId(tenureBand)) {
      alert("Please select how long you have been in your current job or role.");
      return;
    }
    const screening: StudyScreening = {
      participantName: name.trim(),
      tenureBand,
      jobSatisfaction: satisfaction as 1 | 2 | 3 | 4 | 5,
    };
    const err = validateScreening(screening);
    if (err) {
      alert(err);
      return;
    }
    const base = readStudySession() ?? ensureStudySession();
    writeStudySession({ ...base, screening });
    setStep("questionnaire");
  };

  const onStudyPredictSuccess = useCallback(
    (payload: {
      responses: { questionId: number; answerIndex: number }[];
      predictions: { career: string; probability: number }[];
    }) => {
      const base = readStudySession();
      if (!base) return;
      writeStudySession({
        ...base,
        questionnaireResponses: payload.responses,
        predictions: payload.predictions,
        questionnaireSubmittedAt: new Date().toISOString(),
      });
      router.push("/results");
    },
    [router]
  );

  if (!hydrated || restart) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f4f7fa]">
        <div className="text-center text-[#525252]">Loading…</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f4f7fa] px-4 py-5 sm:py-8">
      <div className="mx-auto max-w-3xl">
        <p
          className={`mb-6 text-center text-xs font-medium text-[#4f46e5] sm:mb-8 sm:text-sm ${
            step === "questionnaire" ? "hidden sm:block" : ""
          }`}
        >
          {stepLabel}
        </p>

        {step === "consent" && (
          <div className="overflow-hidden rounded-2xl border border-[#e5e5e5] bg-[#ffffff] shadow-lg">
            <div className="border-b border-[#e5e5e5] p-4 sm:p-6 md:p-8">
              <h1 className="mb-2 text-xl font-bold text-[#0a0a0a] sm:text-2xl">Informed consent</h1>
              <p className="text-sm text-[#525252]">
                Please read carefully before you continue.
              </p>
            </div>
            <div className="max-h-[55vh] space-y-4 overflow-y-auto px-4 py-5 text-sm leading-relaxed text-[#404040] sm:px-6 sm:py-6 md:px-8">
              <p>
                <strong>Purpose.</strong> You are invited to take part in a validation study for a
                college–career field recommendation tool developed for thesis research. We are
                surveying employees who work in one of fourteen career fields to test whether the
                model’s top recommendations align with participants who are already working in
                relevant career areas, especially when they are generally satisfied with their current job.
              </p>
              <p>
                <strong>What you will do.</strong> You will review this consent form, answer a few
                background questions (including your name, time in your current role, and job
                satisfaction), complete a 30-item questionnaire, view
                three recommended college fields, and answer a short follow-up about how those
                recommendations relate to your own field and interests.
              </p>
              <p>
                <strong>Voluntary participation.</strong> Your participation is voluntary. You may
                stop at any time without penalty. If you stop before the end, data collected up to
                that point may still be retained if you already submitted a partial session (see
                data retention below).
              </p>
              <p>
                <strong>Risks and benefits.</strong> There are no direct benefits guaranteed. The
                tool is experimental and not a substitute for career counseling. Minimal risks
                include mild inconvenience and the possibility that written responses could be
                read by the research team.
              </p>
              <p>
                <strong>Confidentiality and data use.</strong> Responses are used for research and
                thesis analysis. Data are stored on the study server (e.g. appended to a restricted
                research file under the project’s{" "}
                <code className="rounded bg-[#f4f4f5] px-1 text-xs text-[#171717]">data/</code>{" "}
                directory). Access is limited to the researcher(s) named in your ethics approval.
                Your <strong>full legal name</strong> is collected on the next screen as an identifier
                for this study, in line with your ethics approval and data-handling procedures.
              </p>
              <p>
                <strong>Contact.</strong> Jourdan Ken D. Catarina,{" "}
                <a
                  href="mailto:jdcatarina@up.edu.ph"
                  className="text-[#4338ca] underline underline-offset-2 hover:text-[#3730a3]"
                >
                  jdcatarina@up.edu.ph
                </a>
                , University of the Philippines Cebu.
              </p>
              <p>
                <strong>Consent.</strong> By checking the box below and continuing, you confirm that
                you are at least 18 years old (or the age of majority in your jurisdiction), you
                have read this information, and you agree to participate under these terms.
              </p>
            </div>
            <div className="space-y-4 border-t border-[#e5e5e5] bg-[#fafafa] p-4 sm:p-6 md:p-8">
              <label className="flex cursor-pointer items-start gap-3">
                <input
                  type="checkbox"
                  checked={consentReadChecked}
                  onChange={(e) => setConsentReadChecked(e.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-[#d4d4d8] text-[#4f46e5] accent-[#4f46e5] focus:ring-2 focus:ring-[#6366f1]"
                />
                <span className="text-sm text-[#262626]">
                  I have read the above, I understand it, and I agree to participate in this study.
                </span>
              </label>
              <button
                type="button"
                disabled={!consentReadChecked}
                onClick={handleConsentContinue}
                className={`w-full rounded-xl py-3 font-semibold transition-all ${
                  consentReadChecked
                    ? "bg-[#4f46e5] text-white shadow-md hover:bg-[#4338ca]"
                    : "cursor-not-allowed bg-[#e5e5e5] text-[#a3a3a3]"
                }`}
              >
                Continue to background questions
              </button>
            </div>
          </div>
        )}

        {step === "screening" && (
          <div className="space-y-5 rounded-2xl border border-[#e5e5e5] bg-[#ffffff] p-4 shadow-lg sm:space-y-6 sm:p-6 md:p-8">
            <h1 className="text-xl font-bold text-[#0a0a0a] sm:text-2xl">About you and your current role</h1>
            <p className="text-sm text-[#525252]">
              These answers help interpret validation results. All items in this section are used
              only for research as described in the consent form.
            </p>

            <div>
              <label htmlFor="participant-name" className="mb-1 block text-sm font-semibold text-[#171717]">
                Full name <span className="text-[#dc2626]">*</span>
              </label>
              <p className="mb-1.5 text-xs leading-relaxed text-[#707070]">
                Enter your complete legal name (given and family name as applicable). Do not use a
                nickname or study code.
              </p>
              <input
                id="participant-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Maria Santos Reyes"
                autoComplete="name"
                inputMode="text"
                className="w-full rounded-lg border border-[#d4d4d8] bg-white px-3 py-2.5 text-sm text-[#171717] placeholder:text-[#a3a3a3] focus:border-[#4f46e5] focus:outline-none focus:ring-2 focus:ring-[#a5b4fc]"
              />
            </div>

            <div className="space-y-2">
              <p id="tenure-field-label" className="text-sm font-semibold text-[#171717]">
                How long have you been in your current job or role? <span className="text-[#dc2626]">*</span>
              </p>
              <p id="tenure-field-hint" className="text-xs leading-relaxed text-[#707070]">
                Open the menu, pick the closest match, then tap outside or press Esc to close. You can
                change your answer before continuing.
              </p>
              <div ref={tenureDropdownRef} className="relative max-w-lg">
                <button
                  type="button"
                  id="tenure-band-trigger"
                  aria-haspopup="listbox"
                  aria-expanded={tenureMenuOpen}
                  aria-controls="tenure-band-listbox"
                  aria-labelledby="tenure-field-label"
                  aria-describedby="tenure-field-hint"
                  onClick={() => setTenureMenuOpen((o) => !o)}
                  className={`flex min-h-[52px] w-full items-center justify-between gap-3 rounded-xl border-2 bg-white px-4 py-3.5 text-left text-[15px] font-medium shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-[#a5b4fc] focus:ring-offset-2 focus:ring-offset-[#f4f7fa] active:scale-[0.998] ${
                    tenureBand
                      ? "border-[#4f46e5] text-[#171717]"
                      : "border-[#d4d4d8] text-[#737373] hover:border-[#a3a3a3]"
                  } ${tenureMenuOpen ? "border-[#4f46e5] ring-2 ring-[#c7d2fe] ring-offset-2 ring-offset-[#f4f7fa]" : ""}`}
                >
                  <span className={tenureBand ? "text-[#171717]" : "text-[#737373]"}>
                    {tenureBand ? TENURE_BAND_LABELS[tenureBand] : "Choose length of time in this role…"}
                  </span>
                  <svg
                    className={`h-5 w-5 shrink-0 text-[#525252] transition-transform duration-200 ${
                      tenureMenuOpen ? "rotate-180" : ""
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {tenureMenuOpen && (
                  <ul
                    id="tenure-band-listbox"
                    role="listbox"
                    aria-labelledby="tenure-field-label"
                    className="absolute left-0 right-0 top-[calc(100%+6px)] z-30 max-h-[min(320px,70vh)] overflow-auto rounded-xl border-2 border-[#e5e5e5] bg-white py-1.5 shadow-xl ring-1 ring-black/5"
                  >
                    {TENURE_BAND_IDS.map((id) => {
                      const selected = tenureBand === id;
                      return (
                        <li key={id} role="presentation" className="px-1.5">
                          <button
                            type="button"
                            role="option"
                            aria-selected={selected}
                            onClick={() => {
                              setTenureBand(id);
                              setTenureMenuOpen(false);
                            }}
                            className={`flex min-h-[48px] w-full items-center justify-between gap-3 rounded-lg px-3.5 py-3 text-left text-sm font-medium transition-colors ${
                              selected
                                ? "bg-[#eef2ff] text-[#312e81]"
                                : "text-[#404040] hover:bg-[#f4f4f5] active:bg-[#ebebeb]"
                            }`}
                          >
                            <span>{TENURE_BAND_LABELS[id]}</span>
                            {selected && (
                              <svg
                                className="h-5 w-5 shrink-0 text-[#4f46e5]"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                aria-hidden="true"
                              >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                              </svg>
                            )}
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </div>

            <div>
              <span className="mb-2 block text-sm font-semibold text-[#171717]">
                Overall, how satisfied are you with your current job? <span className="text-[#dc2626]">*</span>
              </span>
              <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
                {(
                  [
                    [1, "Very dissatisfied"],
                    [2, "Dissatisfied"],
                    [3, "Neutral"],
                    [4, "Satisfied"],
                    [5, "Very satisfied"],
                  ] as const
                ).map(([val, label]) => (
                  <label
                    key={val}
                    className={`min-w-[140px] flex-1 cursor-pointer rounded-lg border-2 px-3 py-2.5 text-center text-sm transition-all ${
                      satisfaction === val
                        ? "border-[#4f46e5] bg-[#eef2ff] font-medium text-[#312e81]"
                        : "border-[#d4d4d8] bg-white text-[#404040] hover:border-[#a3a3a3]"
                    }`}
                  >
                    <input
                      type="radio"
                      name="sat"
                      className="sr-only"
                      checked={satisfaction === val}
                      onChange={() => setSatisfaction(val)}
                    />
                    {label}
                  </label>
                ))}
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => setStep("consent")}
                className="rounded-lg border border-[#d4d4d8] bg-white px-4 py-2 text-sm font-semibold text-[#171717] hover:bg-[#fafafa]"
              >
                Back
              </button>
              <button
                type="button"
                onClick={handleScreeningContinue}
                className="flex-1 rounded-xl bg-[#4f46e5] py-2.5 text-sm font-semibold text-white shadow-md hover:bg-[#4338ca] sm:py-3 sm:text-base"
              >
                Continue to questionnaire
              </button>
            </div>
          </div>
        )}

        {step === "questionnaire" && sessionId && (
          <QuestionnaireClient
            studyProgressKeySuffix={sessionId}
            onStudyPredictSuccess={onStudyPredictSuccess}
          />
        )}
      </div>
    </div>
  );
}
