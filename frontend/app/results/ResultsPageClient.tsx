"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import ResultsCard from "@/components/ResultsCard";
import LoadingSpinner from "@/components/LoadingSpinner";
import Link from "next/link";

interface Prediction {
  career: string;
  probability: number;
  traits?: string[];
  description?: string;
}

const CAREER_DESCRIPTIONS: Record<string, string> = {
  "Engineering": "Engineering programs cover civil, mechanical, electrical, industrial, and other engineering disciplines. Students apply math and science principles to design and build structures, systems, and machines that solve real-world problems.",
  "Computer Science & Technology": "Computer Science & Technology programs include CS, IT, Information Systems, AI, and Cybersecurity. Students learn programming, algorithms, software development, and cutting-edge technologies to solve complex technical challenges.",
  "Business & Management": "Business & Management programs cover business administration, marketing, and entrepreneurship. Students learn leadership, strategic thinking, and organizational management to drive business success.",
  "Accounting & Finance": "Accounting & Finance programs prepare students for careers in accountancy, banking, and financial management. Graduates manage financial records, ensure compliance, and make strategic financial decisions.",
  "Nursing & Allied Health": "Nursing & Allied Health programs include nursing, medical technology, physical therapy, and radiology. Students learn patient care, medical procedures, and healthcare support services.",
  "Medicine (Pre-Med & Medical Fields)": "Medicine programs prepare students for medical careers through biology, pharmaceutical studies, and medical programs. Focus on patient care, diagnosis, and medical excellence.",
  "Education / Teaching": "Education programs train future teachers for elementary, secondary, and special education. Graduates create engaging learning environments and help students develop critical thinking skills.",
  "Psychology & Behavioral Science": "Psychology & Behavioral Science programs explore human behavior, mental processes, and relationships. Students learn research methods and therapeutic approaches to help individuals and communities.",
  "Communication & Media": "Communication & Media programs cover mass communication, journalism, and broadcasting. Students learn to create content, report news, and manage communication strategies across various media platforms.",
  "Law & Legal Studies": "Law & Legal Studies programs train students in legal systems, rights, and justice. Graduates work in courts, legal firms, and organizations to advocate for clients and uphold legal principles.",
  "Architecture & Built Environment": "Architecture & Built Environment programs include architecture and urban planning. Students combine creativity with technical skills to design buildings, spaces, and sustainable urban environments.",
  "Agriculture & Environmental Studies": "Agriculture & Environmental Studies programs focus on sustainable farming, environmental conservation, and natural resource management. Students work with plants, animals, and ecosystems.",
  "Natural Sciences": "Natural Sciences programs cover biology, chemistry, and physics. Students conduct research, experiments, and advance scientific knowledge through systematic investigation and analysis.",
  "Arts & Design": "Arts & Design programs include multimedia arts, graphic design, and fine arts. Students develop creative skills, artistic expression, and design expertise across various visual and digital media.",
};

export default function ResultsPageClient() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const predictionsParam = searchParams.get("predictions");
    if (predictionsParam) {
      try {
        const parsed = JSON.parse(decodeURIComponent(predictionsParam));
        // Ensure we have top 3 predictions
        const top3 = parsed.slice(0, 3);
        // Add descriptions
        const withDescriptions = top3.map((p: Prediction) => ({
          ...p,
          description: CAREER_DESCRIPTIONS[p.career] || "",
        }));
        setPredictions(withDescriptions);
        setLoading(false);
      } catch (e) {
        console.error("Failed to parse predictions", e);
        router.push("/");
      }
    } else {
      router.push("/");
    }
  }, [searchParams, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 py-12 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-block p-4 bg-slate-100 rounded-full mb-4">
            <svg className="w-12 h-12 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
            Your College Field Recommendations
          </h1>
          <p className="text-lg text-gray-600 max-w-xl mx-auto">
            Based on your responses, here are 3 college fields that match your profile
          </p>
          <p className="text-sm text-gray-500 mt-2 italic">
            Listed in no particular order
          </p>
        </div>

        {/* Results Cards */}
        <div className="space-y-5 mb-12">
          {predictions.map((prediction, index) => (
            <ResultsCard
              key={prediction.career}
              career={prediction.career}
              description={prediction.description}
              accentColor={["slate", "teal", "amber"][index] as "slate" | "teal" | "amber"}
            />
          ))}
        </div>

        {/* Next Steps */}
        <div className="bg-white rounded-xl shadow-md p-8 md:p-12 text-center border border-gray-200">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            Next Steps
          </h2>
          <p className="text-gray-600 mb-8 text-lg leading-relaxed max-w-2xl mx-auto">
            Consider exploring these college fields/courses further. Research each option, 
            talk to students and professionals in these fields, and think about which aligns 
            best with your long-term goals and values.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/questionnaire"
              className="px-8 py-4 bg-gray-600 text-white rounded-xl hover:bg-gray-700 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              Retake Questionnaire
            </Link>
            <Link
              href="/"
              className="px-8 py-4 bg-slate-700 text-white rounded-xl hover:bg-slate-800 transition-all duration-200 font-semibold shadow-md hover:shadow-lg"
            >
              Back to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
