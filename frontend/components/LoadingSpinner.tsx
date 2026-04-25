export default function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px]">
      <div className="relative w-20 h-20 mb-6">
        <div className="absolute top-0 left-0 h-full w-full rounded-full border-4 border-[#bfdbfe]" />
        <div className="absolute top-0 left-0 h-full w-full animate-spin rounded-full border-4 border-[#2563eb] border-t-transparent" />
      </div>
      <p className="mb-2 text-xl font-semibold text-[#404040]">Analyzing your responses...</p>
      <p className="text-sm text-[#737373]">This may take a few moments</p>
      <div className="mt-4 flex gap-2">
        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
      </div>
    </div>
  );
}
