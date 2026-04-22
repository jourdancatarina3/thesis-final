import { Suspense } from "react";
import LoadingSpinner from "@/components/LoadingSpinner";
import ResultsPageClient from "./ResultsPageClient";

export default function ResultsPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-stone-50 flex items-center justify-center">
          <LoadingSpinner />
        </div>
      }
    >
      <ResultsPageClient />
    </Suspense>
  );
}
