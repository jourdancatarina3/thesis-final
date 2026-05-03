interface ProgressBarProps {
  current: number;
  total: number;
}

export default function ProgressBar({ current, total }: ProgressBarProps) {
  const percentage = Math.min((current / total) * 100, 100);

  return (
    <div
      className="w-full"
      role="progressbar"
      aria-valuenow={Math.round(percentage)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label="Your progress through this questionnaire"
    >
      <div className="h-3 w-full overflow-hidden rounded-full bg-[#e5e5e5] shadow-inner sm:h-4">
        <div
          className="h-3 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 shadow-md transition-all duration-500 ease-out sm:h-4"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
