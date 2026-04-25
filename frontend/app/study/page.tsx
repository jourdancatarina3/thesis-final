import { Suspense } from "react";
import StudyFlowClient from "./StudyFlowClient";

function StudyFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f4f7fa]">
      <p className="text-[#525252]">Loading study…</p>
    </div>
  );
}

export default function StudyPage() {
  return (
    <Suspense fallback={<StudyFallback />}>
      <StudyFlowClient />
    </Suspense>
  );
}
