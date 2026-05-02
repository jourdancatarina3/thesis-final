interface ProgressBarProps {
  current: number;
  total: number;
}

export default function ProgressBar({ current, total }: ProgressBarProps) {
  const percentage = Math.min((current / total) * 100, 100);

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-2 sm:mb-3">
        <span className="text-xs font-semibold text-[#404040] sm:text-sm">
          Question {current} of {total}
        </span>
        <span className="text-xs font-semibold text-[#404040] sm:text-sm">
          {Math.round(percentage)}%
        </span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-[#e5e5e5] shadow-inner sm:h-4">
        <div
          className="bg-gradient-to-r from-blue-500 to-indigo-600 h-3 sm:h-4 rounded-full transition-all duration-500 ease-out shadow-md"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
