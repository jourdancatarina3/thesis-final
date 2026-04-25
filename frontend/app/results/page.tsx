import { Suspense } from "react";
import LoadingSpinner from "@/components/LoadingSpinner";
import ResultsPageClient from "./ResultsPageClient";

export default function ResultsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-[#fafaf9]">
          <LoadingSpinner />
        </div>
      }
    >
      <ResultsPageClient />
    </Suspense>
  );
}
