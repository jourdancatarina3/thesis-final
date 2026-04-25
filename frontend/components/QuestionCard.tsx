"use client";

interface QuestionCardProps {
  question: {
    id: number;
    question: string;
    options: string[];
  };
  selectedAnswer: number | null;
  onAnswerSelect: (answerIndex: number) => void;
  isAnimating?: boolean;
}

export default function QuestionCard({
  question,
  selectedAnswer,
  onAnswerSelect,
  isAnimating = false,
}: QuestionCardProps) {
  return (
    <div
      className={`rounded-2xl border-2 border-[#e5e5e5] bg-white p-6 shadow-lg transition-all duration-300 md:p-8 ${
        isAnimating ? "opacity-0 scale-95" : "opacity-100 scale-100"
      }`}
    >
      <h2 className="mb-6 text-xl font-bold leading-relaxed text-[#171717] md:text-2xl">
        {question.question}
      </h2>
      <div className="space-y-3">
        {question.options.map((option, index) => {
          const isSelected = selectedAnswer === index;
          return (
            <button
              key={index}
              onClick={() => onAnswerSelect(index)}
              className={`w-full transform rounded-xl border-2 p-4 text-left transition-all duration-200 hover:scale-[1.02] md:p-5 ${
                isSelected
                  ? "border-[#2563eb] bg-gradient-to-r from-[#eff6ff] to-[#eef2ff] shadow-md ring-2 ring-[#bfdbfe]"
                  : "border-[#d4d4d8] bg-white hover:border-[#93c5fd] hover:bg-[#f8fafc] hover:shadow-sm"
              }`}
            >
              <div className="flex items-start gap-4">
                <div
                  className={`mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border-2 transition-all ${
                    isSelected
                      ? "border-[#2563eb] bg-[#2563eb]"
                      : "border-[#d4d4d8] bg-white"
                  }`}
                >
                  {isSelected && (
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
                <span
                  className={`flex-1 text-base md:text-lg ${
                    isSelected ? "font-semibold text-[#1e3a8a]" : "text-[#404040]"
                  }`}
                >
                  {option}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
