import Link from "next/link";

const EXAMPLE_QUERIES = [
  "When can I switch from Stamp 2 to Stamp 1G?",
  "Am I eligible for Jobseeker's Benefit after being made redundant?",
  "What's the VAT registration threshold for SaaS in Ireland?",
  "How do I apply for a PPSN?",
];

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <span className="font-semibold text-gray-900">IE Public Services Advisor</span>
          <span className="text-xs text-gray-500 bg-yellow-50 border border-yellow-200 rounded px-2 py-1">
            v0.1 · Week 1
          </span>
        </div>
      </header>

      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-16">
        <div className="max-w-2xl w-full text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Find your way through Irish public services.
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Every answer grounded in official sources — Revenue, Citizens
            Information, ISD, DSP, HSE — with verifiable citations.
          </p>

          <Link
            href="/chat"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-3 rounded-lg transition-colors mb-12"
          >
            Ask a question →
          </Link>

          {/* Example queries */}
          <div className="text-left">
            <p className="text-sm font-medium text-gray-500 mb-3">Try asking:</p>
            <div className="grid gap-2">
              {EXAMPLE_QUERIES.map((q) => (
                <Link
                  key={q}
                  href={`/chat?q=${encodeURIComponent(q)}`}
                  className="bg-white border border-gray-200 rounded-lg px-4 py-3 text-sm text-gray-700 hover:border-blue-300 hover:bg-blue-50 transition-colors text-left"
                >
                  {q}
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Trust & disclaimer */}
        <div className="mt-12 max-w-2xl w-full">
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-800">
            <strong>⚠️ Important:</strong> This is informational guidance powered by AI, not legal or
            professional advice. Always verify with the relevant authority or a qualified professional.
          </div>
          <p className="mt-3 text-center text-xs text-gray-400">
            Sources: Revenue · Citizens Information · Gov.ie · ISD · DSP · HSE
          </p>
        </div>
      </div>
    </main>
  );
}
