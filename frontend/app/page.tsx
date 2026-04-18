import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 px-4 py-12">
      <main className="w-full max-w-4xl mx-auto text-center">
        <div className="mb-8">
          <h1 className="text-6xl font-bold text-gray-900 mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Career Discovery
          </h1>
          <p className="text-2xl text-gray-700 mb-2 font-medium">
            Discover Your Ideal Career Path
          </p>
          <p className="text-lg text-gray-600 mb-12 max-w-2xl mx-auto leading-relaxed">
            Answer 30 questions about your preferences, values, and work style.
            Our system maps your responses to the same features used by the career dataset model
            and recommends the top 3 college fields or courses that best match your profile.
          </p>
        </div>
        
        <div className="bg-white rounded-2xl shadow-2xl p-8 md:p-12 mb-8 border border-gray-100">
          <h2 className="text-3xl font-semibold text-gray-800 mb-8">
            How It Works
          </h2>
          <div className="grid md:grid-cols-3 gap-8 text-left">
            <div className="flex flex-col items-start">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center text-white font-bold text-2xl mb-4 shadow-lg">
                1
              </div>
              <h3 className="font-bold text-xl text-gray-800 mb-3">Answer Questions</h3>
              <p className="text-gray-600 leading-relaxed">
                Complete the 30-question survey covering behavior, academics, values, and work preferences.
                Your progress is saved as you go.
              </p>
            </div>
            <div className="flex flex-col items-start">
              <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-2xl flex items-center justify-center text-white font-bold text-2xl mb-4 shadow-lg">
                2
              </div>
              <h3 className="font-bold text-xl text-gray-800 mb-3">AI Analysis</h3>
              <p className="text-gray-600 leading-relaxed">
                A gradient-boosted model trained on combined career datasets scores your mapped
                features and ranks the most likely career categories.
              </p>
            </div>
            <div className="flex flex-col items-start">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl flex items-center justify-center text-white font-bold text-2xl mb-4 shadow-lg">
                3
              </div>
              <h3 className="font-bold text-xl text-gray-800 mb-3">Get Recommendations</h3>
              <p className="text-gray-600 leading-relaxed">
                Receive your top 3 career recommendations with detailed insights 
                about why each career matches your profile.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link
            href="/questionnaire"
            className="group relative inline-flex items-center justify-center px-8 py-4 text-lg font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200"
          >
            <span>Start Your Career Discovery Journey</span>
            <svg 
              className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>

          <Link
            href="/questionnaire#paste"
            className="inline-flex items-center justify-center px-6 py-3 text-sm font-semibold text-blue-700 bg-white border border-dashed border-blue-300 rounded-xl shadow-sm hover:bg-blue-50 hover:border-blue-400 transition-all duration-200"
          >
            Paste answers & auto-submit (test)
          </Link>
        </div>

        <p className="mt-8 text-sm text-gray-500 flex items-center justify-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Takes approximately 10-15 minutes to complete
        </p>
      </main>
    </div>
  );
}
