interface ProgressBarProps {
  current: number;
  total: number;
}

export default function ProgressBar({ current, total }: ProgressBarProps) {
  const percentage = Math.min((current / total) * 100, 100);

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-3">
        <span className="text-sm font-semibold text-[#404040]">
          Question {current} of {total}
        </span>
        <span className="text-sm font-semibold text-[#404040]">
          {Math.round(percentage)}%
        </span>
      </div>
      <div className="h-4 w-full overflow-hidden rounded-full bg-[#e5e5e5] shadow-inner">
        <div
          className="bg-gradient-to-r from-blue-500 to-indigo-600 h-4 rounded-full transition-all duration-500 ease-out shadow-md"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
