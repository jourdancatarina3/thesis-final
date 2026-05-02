interface ResultsCardProps {
  career: string;
  description?: string;
  accentColor?: "slate" | "teal" | "amber";
}

const ACCENT_BORDERS = {
  slate: "border-l-slate-500",
  teal: "border-l-teal-500",
  amber: "border-l-amber-500",
};

export default function ResultsCard({ career, description, accentColor = "slate" }: ResultsCardProps) {
  return (
    <div
      className={`overflow-hidden rounded-xl border border-[#e5e5e5] bg-white shadow-md transition-all duration-200 hover:shadow-lg border-l-4 ${ACCENT_BORDERS[accentColor]}`}
    >
      <div className="p-4 md:p-8">
        <h3 className="mb-2 text-lg font-semibold text-[#171717] sm:mb-3 sm:text-xl md:text-2xl">{career}</h3>
        {description && (
          <p className="text-sm leading-relaxed text-[#525252] sm:text-[15px]">{description}</p>
        )}
      </div>
    </div>
  );
}
