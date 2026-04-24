import { Suspense } from "react";
import QuestionnairePasteClient from "./QuestionnairePasteClient";

function PasteFallback() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
      <p className="text-gray-600">Loading…</p>
    </div>
  );
}

export default function QuestionnairePastePage() {
  return (
    <Suspense fallback={<PasteFallback />}>
      <QuestionnairePasteClient />
    </Suspense>
  );
}
