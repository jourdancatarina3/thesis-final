interface ResultsCardProps {
  career: string;
  description?: string;
  /** Calibrated probability from the model (0–1); shown as a "Match confidence" percentage. */
  probability?: number;
  accentColor?: "slate" | "teal" | "amber";
}

const ACCENT_BORDERS = {
  slate: "border-l-slate-500",
  teal: "border-l-teal-500",
  amber: "border-l-amber-500",
};

const ACCENT_BADGES = {
  slate: "bg-slate-100 text-slate-700",
  teal: "bg-teal-100 text-teal-700",
  amber: "bg-amber-100 text-amber-700",
};

function formatConfidence(probability: number): string {
  const pct = Math.round(probability * 100);
  if (pct < 1) return "<1%";
  if (pct > 99 && probability < 1) return ">99%";
  return `${pct}%`;
}

export default function ResultsCard({
  career,
  description,
  probability,
  accentColor = "slate",
}: ResultsCardProps) {
  const showConfidence = typeof probability === "number" && Number.isFinite(probability);

  return (
    <div
      className={`overflow-hidden rounded-xl border border-[#e5e5e5] bg-white shadow-md transition-all duration-200 hover:shadow-lg border-l-4 ${ACCENT_BORDERS[accentColor]}`}
    >
      <div className="p-4 md:p-8">
        <div className="mb-2 flex flex-wrap items-start justify-between gap-x-3 gap-y-2 sm:mb-3">
          <h3 className="text-lg font-semibold text-[#171717] sm:text-xl md:text-2xl">{career}</h3>
          {showConfidence && (
            <span
              className={`inline-flex shrink-0 items-center rounded-full px-3 py-1 text-xs font-semibold sm:text-sm ${ACCENT_BADGES[accentColor]}`}
              title="Calibrated probability from the model"
            >
              Match confidence: {formatConfidence(probability)}
            </span>
          )}
        </div>
        {description && (
          <p className="text-sm leading-relaxed text-[#525252] sm:text-[15px]">{description}</p>
        )}
      </div>
    </div>
  );
}
