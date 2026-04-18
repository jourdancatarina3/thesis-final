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
      className={`bg-white rounded-2xl shadow-lg p-6 md:p-8 border-2 border-gray-100 transition-all duration-300 ${
        isAnimating ? 'opacity-0 scale-95' : 'opacity-100 scale-100'
      }`}
    >
      <h2 className="text-xl md:text-2xl font-bold text-gray-800 mb-6 leading-relaxed">
        {question.question}
      </h2>
      <div className="space-y-3">
        {question.options.map((option, index) => {
          const isSelected = selectedAnswer === index;
          return (
            <button
              key={index}
              onClick={() => onAnswerSelect(index)}
              className={`w-full text-left p-4 md:p-5 rounded-xl border-2 transition-all duration-200 transform hover:scale-[1.02] ${
                isSelected
                  ? "border-blue-600 bg-gradient-to-r from-blue-50 to-indigo-50 shadow-md ring-2 ring-blue-200"
                  : "border-gray-200 hover:border-blue-300 hover:bg-blue-50/50 hover:shadow-sm"
              }`}
            >
              <div className="flex items-start gap-4">
                <div
                  className={`flex-shrink-0 w-6 h-6 rounded-full border-2 mt-0.5 flex items-center justify-center transition-all ${
                    isSelected
                      ? "border-blue-600 bg-blue-600"
                      : "border-gray-300 bg-white"
                  }`}
                >
                  {isSelected && (
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
                <span
                  className={`text-base md:text-lg flex-1 ${
                    isSelected ? "text-blue-900 font-semibold" : "text-gray-700"
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
