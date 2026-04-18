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
    <div className={`bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-all duration-200 border border-gray-200 border-l-4 ${ACCENT_BORDERS[accentColor]}`}>
      <div className="p-6 md:p-8">
        <h3 className="text-xl md:text-2xl font-semibold text-gray-900 mb-3">{career}</h3>
        {description && (
          <p className="text-gray-600 text-[15px] leading-relaxed">{description}</p>
        )}
      </div>
    </div>
  );
}
