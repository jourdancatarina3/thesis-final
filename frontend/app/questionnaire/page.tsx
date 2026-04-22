import { Suspense } from "react";
import QuestionnaireClient from "./QuestionnaireClient";

function QuestionnaireFallback() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
      <div className="text-center">
        <div className="relative w-16 h-16 mx-auto mb-4">
          <div className="absolute top-0 left-0 w-full h-full border-4 border-blue-200 rounded-full" />
          <div className="absolute top-0 left-0 w-full h-full border-4 border-blue-600 rounded-full border-t-transparent animate-spin" />
        </div>
        <p className="text-gray-600 text-lg">Loading questionnaire...</p>
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
