import { Suspense } from "react";
import QuestionnaireClient from "./QuestionnaireClient";

function QuestionnaireFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#eff6ff] via-[#eef2ff] to-[#faf5ff]">
      <div className="text-center">
        <div className="relative mx-auto mb-4 h-16 w-16">
          <div className="absolute left-0 top-0 h-full w-full rounded-full border-4 border-[#bfdbfe]" />
          <div className="absolute left-0 top-0 h-full w-full animate-spin rounded-full border-4 border-[#2563eb] border-t-transparent" />
        </div>
        <p className="text-lg text-[#525252]">Loading questionnaire...</p>
      </div>
    </div>
  );
}

export default function QuestionnairePage() {
  return (
    <Suspense fallback={<QuestionnaireFallback />}>
      <QuestionnaireClient />
    </Suspense>
  );
}
