import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 px-4 py-8 sm:py-12">
      <main className="w-full max-w-4xl mx-auto text-center">
        <div className="mb-6 sm:mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-3 sm:mb-4 sm:text-4xl md:text-5xl lg:text-6xl bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Career field validation study
          </h1>
          <p className="text-lg text-gray-700 mb-2 font-medium sm:text-xl md:text-2xl">
            Help validate a college-field recommendation model
          </p>
          <p className="text-base text-gray-600 mb-8 max-w-2xl mx-auto leading-relaxed sm:mb-12 sm:text-lg">
            This survey is for employees in one of fourteen career fields. You will review a short
            consent form, answer a few background questions, complete 30 preference items, see three
            model-generated college-field recommendations, and answer a brief follow-up about how
            those recommendations relate to your current role. Your responses are saved for thesis
            research only as described in the consent text.
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-2xl p-5 sm:p-8 md:p-12 mb-6 sm:mb-8 border border-gray-100">
          <h2 className="text-2xl font-semibold text-gray-800 mb-6 sm:mb-8 sm:text-3xl">
            How it works
          </h2>
          <div className="grid md:grid-cols-3 gap-6 sm:gap-8 text-left">
            <div className="flex flex-col items-start">
              <div className="w-12 h-12 sm:w-16 sm:h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center text-white font-bold text-xl sm:text-2xl mb-3 sm:mb-4 shadow-lg">
                1
              </div>
              <h3 className="font-bold text-lg text-gray-800 mb-2 sm:mb-3 sm:text-xl">Consent and background</h3>
              <p className="text-gray-600 leading-relaxed">
                Read the informed consent, confirm participation, then share your name, time in your
                current role, and job satisfaction.
              </p>
            </div>
            <div className="flex flex-col items-start">
              <div className="w-12 h-12 sm:w-16 sm:h-16 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-2xl flex items-center justify-center text-white font-bold text-xl sm:text-2xl mb-3 sm:mb-4 shadow-lg">
                2
              </div>
              <h3 className="font-bold text-lg text-gray-800 mb-2 sm:mb-3 sm:text-xl">Questionnaire and model</h3>
              <p className="text-gray-600 leading-relaxed">
                Complete 30 questions about preferences and work style. Your answers are mapped to
                features and scored by a gradient-boosted model trained on combined career datasets.
              </p>
            </div>
            <div className="flex flex-col items-start">
              <div className="w-12 h-12 sm:w-16 sm:h-16 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl flex items-center justify-center text-white font-bold text-xl sm:text-2xl mb-3 sm:mb-4 shadow-lg">
                3
              </div>
              <h3 className="font-bold text-lg text-gray-800 mb-2 sm:mb-3 sm:text-xl">Recommendations and validation</h3>
              <p className="text-gray-600 leading-relaxed">
                View your top three college-field recommendations, then answer a short validation
                section so we can measure how the recommendations relate to your role and interests.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link
            href="/study"
            className="group relative inline-flex items-center justify-center px-6 py-3 text-base font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 sm:px-8 sm:py-4 sm:text-lg"
          >
            <span>Begin validation survey</span>
            <svg
              className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
        </div>
      </main>
    </div>
  );
}
