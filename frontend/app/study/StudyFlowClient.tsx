"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import QuestionnaireClient from "@/app/questionnaire/QuestionnaireClient";
import {
  CONSENT_VERSION,
  ensureStudySession,
  readStudySession,
  validateScreening,
  writeStudySession,
  type StudyScreening,
  type StudySession,
} from "@/lib/studySession";
import { TARGET_CAREERS, type TargetCareer } from "@/lib/targetCareers";

type FlowStep = "consent" | "screening" | "questionnaire";

function inferStep(session: StudySession): FlowStep {
  if (!session.consentAccepted) return "consent";
  if (!session.screening) return "screening";
  if (!session.predictions?.length) return "questionnaire";
  return "questionnaire";
}

const EDUCATION_OPTIONS = [
  "",
  "High school or equivalent",
  "Some college / associate coursework",
  "Bachelor's degree",
  "Master's degree or higher",
  "Doctorate / professional degree",
  "Prefer not to say",
];

export default function StudyFlowClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [step, setStep] = useState<FlowStep>("consent");
  const [consentReadChecked, setConsentReadChecked] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  const [name, setName] = useState("");
  const [tenureYears, setTenureYears] = useState("");
  const [tenureMonths, setTenureMonths] = useState("");
  const [satisfaction, setSatisfaction] = useState<1 | 2 | 3 | 4 | 5 | 0>(0);
  const [careerField, setCareerField] = useState<TargetCareer | "">("");
  const [jobTitle, setJobTitle] = useState("");
  const [workExpYears, setWorkExpYears] = useState("");
  const [educationLevel, setEducationLevel] = useState("");
  const [sessionId, setSessionId] = useState("");

  const restart = searchParams.get("restart") === "1";

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
      setTenureYears(String(session.screening.tenureYears));
      setTenureMonths(String(session.screening.tenureMonths));
      setSatisfaction(session.screening.jobSatisfaction);
      setCareerField(session.screening.selfReportedCareerField);
      setJobTitle(session.screening.jobTitle);
      setWorkExpYears(session.screening.totalWorkExperienceYears);
      setEducationLevel(session.screening.educationLevel);
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
    const y = Math.max(0, parseInt(tenureYears, 10) || 0);
    const m = Math.max(0, Math.min(11, parseInt(tenureMonths, 10) || 0));
    const totalMonths = y * 12 + m;
    if (!careerField) {
      alert("Please select your current career field.");
      return;
    }
    const screening: StudyScreening = {
      participantName: name.trim(),
      tenureYears: y,
      tenureMonths: m,
      totalMonthsTenure: totalMonths,
      jobSatisfaction: satisfaction as 1 | 2 | 3 | 4 | 5,
      selfReportedCareerField: careerField,
      jobTitle: jobTitle.trim(),
      totalWorkExperienceYears: workExpYears.trim(),
      educationLevel: educationLevel.trim(),
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
    <div className="min-h-screen bg-[#f4f7fa] px-4 py-8">
      <div className="mx-auto max-w-3xl">
        <p className="mb-2 text-center text-sm font-medium text-[#4f46e5]">{stepLabel}</p>
        <p className="mb-8 text-center text-xs text-[#707070]">
          Research validation survey — approximately 12–18 minutes
        </p>

        {step === "consent" && (
          <div className="overflow-hidden rounded-2xl border border-[#e5e5e5] bg-[#ffffff] shadow-lg">
            <div className="border-b border-[#e5e5e5] p-6 md:p-8">
              <h1 className="mb-2 text-2xl font-bold text-[#0a0a0a]">Informed consent</h1>
              <p className="text-sm text-[#525252]">
                Please read carefully before you continue. Replace bracketed placeholders with your
                institution and contact details before deployment.
              </p>
            </div>
            <div className="max-h-[55vh] space-y-4 overflow-y-auto px-6 py-6 text-sm leading-relaxed text-[#404040] md:px-8">
              <p>
                <strong>Purpose.</strong> You are invited to take part in a validation study for a
                college–career field recommendation tool developed for thesis research. We are
                surveying employees who work in one of fourteen career fields to test whether the
                model’s top recommendations align with participants’ self-reported field, especially
                when they are generally satisfied with their current job.
              </p>
              <p>
                <strong>What you will do.</strong> You will review this consent form, answer a few
                background questions (including your name, time in your current role, job
                satisfaction, and your current career field), complete a 30-item questionnaire, view
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
                Your <strong>name is an identifier</strong>; if you prefer less identifiable linkage,
                you may use a study code agreed with the researcher instead of your legal name.
              </p>
              <p>
                <strong>Ethics review.</strong> This study should be conducted in line with your
                institution’s ethics / IRB requirements. [Insert IRB or ethics approval reference,
                or state if exempt, as applicable.]
              </p>
              <p>
                <strong>Contact.</strong> [Principal investigator name, email, and institution.]
              </p>
              <p>
                <strong>Consent.</strong> By checking the box below and continuing, you confirm that
                you are at least 18 years old (or the age of majority in your jurisdiction), you
                have read this information, and you agree to participate under these terms.
              </p>
            </div>
            <div className="space-y-4 border-t border-[#e5e5e5] bg-[#fafafa] p-6 md:p-8">
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
          <div className="space-y-6 rounded-2xl border border-[#e5e5e5] bg-[#ffffff] p-6 shadow-lg md:p-8">
            <h1 className="text-2xl font-bold text-[#0a0a0a]">About you and your current role</h1>
            <p className="text-sm text-[#525252]">
              These answers help interpret validation results. All items in this section are used
              only for research as described in the consent form.
            </p>

            <div>
              <label htmlFor="participant-name" className="mb-1 block text-sm font-semibold text-[#171717]">
                Full name or study code <span className="text-[#dc2626]">*</span>
              </label>
              <input
                id="participant-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-lg border border-[#d4d4d8] bg-white px-3 py-2 text-sm text-[#171717] placeholder:text-[#737373] focus:border-[#4f46e5] focus:outline-none focus:ring-2 focus:ring-[#a5b4fc]"
                autoComplete="name"
              />
            </div>

            <div>
              <span className="mb-2 block text-sm font-semibold text-[#171717]">
                How long have you been in your current job or role? <span className="text-[#dc2626]">*</span>
              </span>
              <div className="flex flex-wrap gap-4 items-end">
                <div>
                  <label htmlFor="ty" className="mb-1 block text-xs text-[#707070]">
                    Years
                  </label>
                  <input
                    id="ty"
                    type="number"
                    min={0}
                    value={tenureYears}
                    onChange={(e) => setTenureYears(e.target.value)}
                    className="w-24 rounded-lg border border-[#d4d4d8] bg-white px-3 py-2 text-sm text-[#171717] focus:border-[#4f46e5] focus:outline-none focus:ring-2 focus:ring-[#a5b4fc]"
                  />
                </div>
                <div>
                  <label htmlFor="tm" className="mb-1 block text-xs text-[#707070]">
                    Additional months (0–11)
                  </label>
                  <input
                    id="tm"
                    type="number"
                    min={0}
                    max={11}
                    value={tenureMonths}
                    onChange={(e) => setTenureMonths(e.target.value)}
                    className="w-24 rounded-lg border border-[#d4d4d8] bg-white px-3 py-2 text-sm text-[#171717] focus:border-[#4f46e5] focus:outline-none focus:ring-2 focus:ring-[#a5b4fc]"
                  />
                </div>
              </div>
              <p className="mt-1 text-xs text-[#707070]">
                Enter at least one non-zero value between years and months.
              </p>
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

            <div>
              <label htmlFor="career-field" className="mb-1 block text-sm font-semibold text-[#171717]">
                Which career field best describes your current job? <span className="text-[#dc2626]">*</span>
              </label>
              <select
                id="career-field"
                value={careerField}
                onChange={(e) => setCareerField(e.target.value as TargetCareer | "")}
                className="w-full rounded-lg border border-[#d4d4d8] bg-white px-3 py-2 text-sm text-[#171717] focus:border-[#4f46e5] focus:outline-none focus:ring-2 focus:ring-[#a5b4fc]"
              >
                <option value="">Select one…</option>
                {TARGET_CAREERS.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="job-title" className="mb-1 block text-sm font-semibold text-[#171717]">
                Current job title <span className="font-normal text-[#a3a3a3]">(optional)</span>
              </label>
              <input
                id="job-title"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                className="w-full rounded-lg border border-[#d4d4d8] bg-white px-3 py-2 text-sm text-[#171717] placeholder:text-[#737373] focus:border-[#4f46e5] focus:outline-none focus:ring-2 focus:ring-[#a5b4fc]"
              />
            </div>

            <div>
              <label htmlFor="work-exp" className="mb-1 block text-sm font-semibold text-[#171717]">
                Total years of work experience <span className="font-normal text-[#a3a3a3]">(optional)</span>
              </label>
              <input
                id="work-exp"
                type="number"
                min={0}
                step={0.5}
                value={workExpYears}
                onChange={(e) => setWorkExpYears(e.target.value)}
                placeholder="e.g. 8"
                className="w-full max-w-xs rounded-lg border border-[#d4d4d8] bg-white px-3 py-2 text-sm text-[#171717] placeholder:text-[#737373] focus:border-[#4f46e5] focus:outline-none focus:ring-2 focus:ring-[#a5b4fc]"
              />
            </div>

            <div>
              <label htmlFor="edu" className="mb-1 block text-sm font-semibold text-[#171717]">
                Highest education level <span className="font-normal text-[#a3a3a3]">(optional)</span>
              </label>
              <select
                id="edu"
                value={educationLevel}
                onChange={(e) => setEducationLevel(e.target.value)}
                className="w-full rounded-lg border border-[#d4d4d8] bg-white px-3 py-2 text-sm text-[#171717] focus:border-[#4f46e5] focus:outline-none focus:ring-2 focus:ring-[#a5b4fc]"
              >
                {EDUCATION_OPTIONS.map((opt) => (
                  <option key={opt || "unset"} value={opt}>
                    {opt || "Select…"}
                  </option>
                ))}
              </select>
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
                className="flex-1 rounded-xl bg-[#4f46e5] py-3 font-semibold text-white shadow-md hover:bg-[#4338ca]"
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
