"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import QuestionCard from "@/components/QuestionCard";
import ProgressBar from "@/components/ProgressBar";

interface QuestionnaireQuestion {
  id: number;
  category: string;
  question: string;
  options: string[];
}

interface QuestionnaireData {
  title: string;
  description: string;
  total_questions: number;
  questions: QuestionnaireQuestion[];
}

// Fisher-Yates shuffle algorithm
// Returns shuffled array and mapping: mapping[shuffledIndex] = originalIndex
function shuffleArray<T>(array: T[]): { shuffled: T[]; mapping: number[] } {
  const shuffled: T[] = [];
  const mapping: number[] = [];
  const indices = array.map((_, i) => i);
  
  // Shuffle the indices using Fisher-Yates
  for (let i = indices.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [indices[i], indices[j]] = [indices[j], indices[i]];
  }
  
  // Create shuffled array and mapping
  // mapping[shuffledIndex] = originalIndex
  for (let shuffledIdx = 0; shuffledIdx < indices.length; shuffledIdx++) {
    const originalIdx = indices[shuffledIdx];
    shuffled[shuffledIdx] = array[originalIdx];
    mapping[shuffledIdx] = originalIdx;
  }
  
  return { shuffled, mapping };
}

export default function QuestionnaireClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isAutoTest = searchParams.get("autoTest") === "1";

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [questionnaire, setQuestionnaire] = useState<QuestionnaireData | null>(null);
  const [answers, setAnswers] = useState<number[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [optionMappings, setOptionMappings] = useState<number[][]>([]); // For each question: shuffledIndex -> originalIndex
  const [hasAutoSubmitted, setHasAutoSubmitted] = useState(false);
  const [pastedAnswers, setPastedAnswers] = useState("");

  // Shuffle options for each question and store mappings
  const shuffledQuestionnaire = useMemo(() => {
    if (!questionnaire) return null;
    
    const shuffled = { ...questionnaire };
    const mappings: number[][] = [];
    
    shuffled.questions = questionnaire.questions.map((q: QuestionnaireQuestion) => {
      const { shuffled: shuffledOptions, mapping } = shuffleArray(q.options);
      mappings.push(mapping);
      return { ...q, options: shuffledOptions };
    });
    
    setOptionMappings(mappings);
    return shuffled;
  }, [questionnaire]);

  // Load questionnaire data
  useEffect(() => {
    fetch("/questionnaire.json")
      .then((res) => res.json())
      .then((data) => {
        setQuestionnaire(data);
        setAnswers(new Array(data.total_questions).fill(null));
      })
      .catch((err) => {
        console.error("Failed to load questionnaire:", err);
        alert("Failed to load questionnaire. Please refresh the page.");
      });
  }, []);

  // Load saved progress from localStorage (skip if auto test mode)
  useEffect(() => {
    if (!questionnaire || optionMappings.length === 0 || isAutoTest) return;
    const saved = localStorage.getItem("questionnaire_progress");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.answers.length === questionnaire.total_questions) {
          setAnswers(parsed.answers);
          // Find first unanswered question
          const firstUnanswered = parsed.answers.findIndex((a: number) => a === null);
          if (firstUnanswered !== -1) {
            setCurrentQuestionIndex(firstUnanswered);
          } else {
            setCurrentQuestionIndex(questionnaire.total_questions - 1);
          }
        }
      } catch (e) {
        console.error("Failed to load saved progress", e);
      }
    }
  }, [questionnaire, optionMappings, isAutoTest]);

  // Save progress to localStorage
  useEffect(() => {
    if (questionnaire && answers.length > 0) {
      localStorage.setItem(
        "questionnaire_progress",
        JSON.stringify({ answers, currentQuestionIndex })
      );
    }
  }, [answers, currentQuestionIndex, questionnaire]);

  const handleSubmit = useCallback(
    async (answersToSubmit?: number[]) => {
      if (!questionnaire) return;

      const finalAnswers = answersToSubmit || answers;

      // Check if all questions are answered
      if (finalAnswers.some((a) => a === null)) {
        alert("Please answer all questions before submitting.");
        return;
      }

      setIsSubmitting(true);

      try {
        // Prepare responses in the format expected by the API
        const responses = questionnaire.questions.map((q: QuestionnaireQuestion, idx: number) => ({
          questionId: q.id,
          answerIndex: finalAnswers[idx],
        }));

        const response = await fetch("/api/predict", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ responses }),
        });

        if (!response.ok) {
          throw new Error("Failed to get predictions");
        }

        const data = await response.json();
        
        // Clear saved progress
        localStorage.removeItem("questionnaire_progress");
        
        // Navigate to results page with predictions
        router.push(
          `/results?predictions=${encodeURIComponent(
            JSON.stringify(data.predictions)
          )}`
        );
      } catch (error) {
        console.error("Error submitting questionnaire:", error);
        alert("An error occurred. Please try again.");
        setIsSubmitting(false);
      }
    },
    [questionnaire, router, answers]
  );

  // Auto-advance after selecting an answer
  const handleAnswerSelect = useCallback(
    (shuffledAnswerIndex: number) => {
      if (!questionnaire) return;

      // Convert shuffled index to original index using the mapping
      const originalIndex =
        optionMappings[currentQuestionIndex]?.[shuffledAnswerIndex] ??
        shuffledAnswerIndex;
      const newAnswers = [...answers];
      newAnswers[currentQuestionIndex] = originalIndex;
      setAnswers(newAnswers);

      // Auto-advance to next question after a short delay
      setTimeout(() => {
        setIsAnimating(true);
        setTimeout(() => {
          if (currentQuestionIndex < questionnaire.total_questions - 1) {
            setCurrentQuestionIndex(currentQuestionIndex + 1);
            setIsAnimating(false);
            // Scroll to top smoothly
            window.scrollTo({ top: 0, behavior: "smooth" });
          } else {
            // Last question answered, submit automatically
            setIsAnimating(false);
            handleSubmit(newAnswers);
          }
        }, 300);
      }, 500);
    },
    [answers, currentQuestionIndex, questionnaire, optionMappings, handleSubmit]
  );

  // Auto-fill and submit in test mode using the provided 30 answers
  useEffect(() => {
    if (!questionnaire || !isAutoTest || hasAutoSubmitted) return;

    const testAnswerTexts = [
      "Writing code or scripts to solve it systematically",
      "Build something functional that solves a real problem",
      "Use statistical methods to find patterns",
      "Working independently on focused tasks",
      "Freedom to experiment and try different approaches",
      "Using specialized knowledge or technical skills",
      "Using software and digital tools",
      "Logical reasoning and mathematical calculations",
      "Solve complex problems step by step",
      "How technology and software function",
      "The technical expert who handles complex parts",
      "Problem-solving and analysis",
      "Science and technical subjects",
      "Solving complex technical challenges",
      "I complete a challenging technical project",
      "Building and creating innovative solutions",
      "The innovations I've contributed",
      "Challenges me intellectually",
      "Writing code and debugging software",
      "Computers and software systems",
      "Solving a complex algorithm or system problem",
      "My code runs without errors",
      "Use specialized technical knowledge",
      "Work independently on focused tasks",
      "Help someone solve a technical problem",
      "Learn new technologies or methods",
      "Develop and test new software features",
      "Breaking it down into smaller, manageable parts",
      "Work through them methodically step by step",
      "Understand why it happened",
    ];

    if (testAnswerTexts.length !== questionnaire.total_questions) {
      console.error(
        "Test answers length does not match total questions.",
        testAnswerTexts.length,
        questionnaire.total_questions
      );
      return;
    }

    try {
      const presetAnswers: number[] = questionnaire.questions.map(
        (q: QuestionnaireQuestion, idx: number) => {
          const desired = testAnswerTexts[idx];
          const optionIndex = q.options.indexOf(desired);
          if (optionIndex === -1) {
            throw new Error(
              `Test answer not found for question ${q.id}: "${desired}"`
            );
          }
          return optionIndex;
        }
      );

      setHasAutoSubmitted(true);
      handleSubmit(presetAnswers);
    } catch (e) {
      console.error("Failed to auto-submit test answers:", e);
      alert(
        "Failed to run the preset test answers. Please check the configuration."
      );
    }
  }, [questionnaire, isAutoTest, hasAutoSubmitted, handleSubmit]);

  const handlePastedAnswersSubmit = useCallback(() => {
    if (!questionnaire) {
      alert("Questionnaire not loaded yet.");
      return;
    }

    const lines = pastedAnswers
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    if (lines.length !== questionnaire.total_questions) {
      alert(
        `Please provide exactly ${questionnaire.total_questions} non-empty lines. You provided ${lines.length}.`
      );
      return;
    }

    try {
      const presetAnswers: number[] = questionnaire.questions.map(
        (q: QuestionnaireQuestion, idx: number) => {
          const desired = lines[idx];
          // Try exact match first
          let optionIndex = q.options.indexOf(desired);

          // If not found, try case-insensitive match
          if (optionIndex === -1) {
            const lowerDesired = desired.toLowerCase();
            optionIndex = q.options.findIndex(
              (opt: string) => opt.toLowerCase() === lowerDesired
            );
          }

          if (optionIndex === -1) {
            throw new Error(
              `Could not find an option matching your answer for question ${q.id}:\n"${desired}"`
            );
          }

          return optionIndex;
        }
      );

      setAnswers(presetAnswers);
      setCurrentQuestionIndex(questionnaire.total_questions - 1);
      handleSubmit(presetAnswers);
    } catch (e: unknown) {
      console.error("Failed to submit pasted answers:", e);
      const msg =
        e instanceof Error ? e.message : "Failed to submit pasted answers. Please check them.";
      alert(msg);
    }
  }, [questionnaire, pastedAnswers, handleSubmit]);

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setIsAnimating(true);
      setTimeout(() => {
        setCurrentQuestionIndex(currentQuestionIndex - 1);
        setIsAnimating(false);
        window.scrollTo({ top: 0, behavior: "smooth" });
      }, 300);
    }
  };

  if (!questionnaire || !shuffledQuestionnaire || optionMappings.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute top-0 left-0 w-full h-full border-4 border-blue-200 rounded-full"></div>
            <div className="absolute top-0 left-0 w-full h-full border-4 border-blue-600 rounded-full border-t-transparent animate-spin"></div>
          </div>
          <p className="text-gray-600 text-lg">Loading questionnaire...</p>
        </div>
      </div>
    );
  }

  const currentQuestion = shuffledQuestionnaire.questions[currentQuestionIndex];
  const isLastQuestion = currentQuestionIndex === questionnaire.total_questions - 1;
  const allAnswered = answers.every((a) => a !== null);
  
  // Convert original answer index to shuffled index for display
  const getShuffledAnswerIndex = (originalIndex: number | null): number | null => {
    if (originalIndex === null) return null;
    const mapping = optionMappings[currentQuestionIndex];
    if (!mapping) return originalIndex;
    // Find the shuffled index that maps to this original index
    return mapping.findIndex((origIdx) => origIdx === originalIndex);
  };
  
  const shuffledSelectedAnswer = getShuffledAnswerIndex(answers[currentQuestionIndex]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
            {shuffledQuestionnaire.title}
          </h1>
          <p className="text-gray-600">
            {shuffledQuestionnaire.description}
          </p>
        </div>

        {/* Progress Bar */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-6 border border-gray-100">
          <ProgressBar
            current={currentQuestionIndex + 1}
            total={shuffledQuestionnaire.total_questions}
          />
        </div>

        {/* Question Card */}
        <div className="mb-8">
          <QuestionCard
            question={currentQuestion}
            selectedAnswer={shuffledSelectedAnswer}
            onAnswerSelect={handleAnswerSelect}
            isAnimating={isAnimating}
          />
        </div>

        {/* Navigation */}
        <div className="flex flex-col gap-6">
          <div className="flex justify-between items-center bg-white rounded-xl shadow-md p-6 border border-gray-100">
            <button
              onClick={handlePrevious}
              disabled={currentQuestionIndex === 0 || isSubmitting}
              className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 flex items-center gap-2 ${
                currentQuestionIndex === 0 || isSubmitting
                  ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                  : "bg-gray-600 text-white hover:bg-gray-700 hover:shadow-lg transform hover:-translate-y-0.5"
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Previous
            </button>

            <div className="text-sm text-gray-500 font-medium">
              {currentQuestionIndex + 1} / {shuffledQuestionnaire.total_questions}
            </div>

            {isLastQuestion && allAnswered && (
              <button
                onClick={() => handleSubmit()}
                disabled={isSubmitting}
                className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 flex items-center gap-2 ${
                  isSubmitting
                    ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                    : "bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg transform hover:-translate-y-0.5"
                }`}
              >
                {isSubmitting ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Submitting...
                  </>
                ) : (
                  <>
                    Submit & Get Results
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </>
                )}
              </button>
            )}
          </div>

          {/* Testing: paste answers */}
          <div
            id="paste"
            className="bg-white rounded-xl shadow-md p-6 border border-dashed border-blue-200"
          >
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-gray-700">
                Testing: paste 30 answers (one per line)
              </h2>
              <span className="text-[11px] uppercase tracking-wide text-blue-500 font-semibold">
                For development use
              </span>
            </div>
            <p className="text-xs text-gray-500 mb-3">
              Paste your answers in order from question 1 to {questionnaire.total_questions}. Each line must
              exactly match one of the options for that question.
            </p>
            <textarea
              value={pastedAnswers}
              onChange={(e) => setPastedAnswers(e.target.value)}
              className="w-full h-40 text-sm border border-gray-200 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 resize-y"
              placeholder="Line 1: answer to question 1&#10;Line 2: answer to question 2&#10;...&#10;Line 30: answer to question 30"
            />
            <div className="mt-3 flex justify-end">
              <button
                type="button"
                onClick={handlePastedAnswersSubmit}
                disabled={isSubmitting || !pastedAnswers.trim()}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${
                  isSubmitting || !pastedAnswers.trim()
                    ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                    : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-md"
                }`}
              >
                Fill and submit from pasted answers
              </button>
            </div>
          </div>

          {/* Helpful hint */}
          {!isLastQuestion && (
            <div className="text-center">
              <p className="text-sm text-gray-500">
                💡 Select an answer to automatically proceed to the next question
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
