"use client";

import type { Citation, Message } from "@/types";

function CitationChip({ citation }: { citation: Citation }) {
  return (
    <a
      href={citation.url}
      target="_blank"
      rel="noopener noreferrer"
      title={citation.snippet}
      className="inline-flex items-center gap-1 text-xs bg-blue-50 border border-blue-200 text-blue-700 rounded px-1.5 py-0.5 hover:bg-blue-100 transition-colors"
    >
      [{citation.n}] {citation.title}
    </a>
  );
}

export function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div className={`max-w-[80%] ${isUser ? "order-2" : "order-1"}`}>
        {/* Role label */}
        <p className={`text-xs font-medium mb-1 ${isUser ? "text-right text-gray-400" : "text-gray-500"}`}>
          {isUser ? "You" : "Advisor"}
        </p>

        {/* Message bubble */}
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? "bg-blue-600 text-white rounded-tr-sm"
              : "bg-white border border-gray-200 text-gray-900 rounded-tl-sm shadow-sm"
          } ${message.isStreaming ? "streaming-cursor" : ""}`}
        >
          {message.content || (message.isStreaming ? "" : "…")}
        </div>

        {/* Citations — shown below the assistant bubble after generation completes */}
        {!isUser && message.citations && message.citations.length > 0 && !message.isStreaming && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            <span className="text-xs text-gray-400 self-center">Sources:</span>
            {message.citations.map((c) => (
              <CitationChip key={c.n} citation={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
