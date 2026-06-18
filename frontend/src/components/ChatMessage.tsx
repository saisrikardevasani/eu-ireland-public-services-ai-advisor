"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import type { Citation, Message } from "@/types";

function CitationChip({ citation }: { citation: Citation }) {
  const dateLabel = citation.crawled_at
    ? new Date(citation.crawled_at).toLocaleDateString("en-IE", { month: "short", year: "numeric" })
    : null;

  return (
    <a
      href={citation.url}
      target="_blank"
      rel="noopener noreferrer"
      title={citation.snippet}
      className="inline-flex items-center gap-1.5 text-xs bg-forest-50 border border-forest-200 text-forest-700 rounded-md px-2 py-1 hover:bg-forest-100 transition-colors font-medium"
    >
      <span>[{citation.n}] {citation.title}</span>
      {dateLabel && (
        <span className="text-forest-400 font-normal border-l border-forest-200 pl-1.5">{dateLabel}</span>
      )}
    </a>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <button
      onClick={handleCopy}
      title="Copy answer"
      className="p-1.5 rounded text-stone-400 hover:text-stone-600 hover:bg-stone-100 transition-colors"
    >
      {copied ? (
        <svg className="w-3.5 h-3.5 text-forest-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      )}
    </button>
  );
}

function ShareButton({ question }: { question?: string }) {
  const [shared, setShared] = useState(false);

  function handleShare() {
    if (!question) return;
    const url = `${window.location.origin}/chat?q=${encodeURIComponent(question)}`;
    navigator.clipboard.writeText(url);
    setShared(true);
    setTimeout(() => setShared(false), 2000);
  }

  if (!question) return null;

  return (
    <button
      onClick={handleShare}
      title="Copy shareable link"
      className="p-1.5 rounded text-stone-400 hover:text-stone-600 hover:bg-stone-100 transition-colors"
    >
      {shared ? (
        <svg className="w-3.5 h-3.5 text-forest-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
      )}
    </button>
  );
}

async function hashQuestion(question: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(question));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
}

function FeedbackButtons({ question }: { question?: string }) {
  const [voted, setVoted] = useState<1 | -1 | null>(null);

  if (!question) return null;

  async function submit(rating: 1 | -1) {
    if (voted !== null) return;
    setVoted(rating);
    try {
      const hash = await hashQuestion(question!);
      await fetch("/api/v1/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question_hash: hash, rating }),
      });
    } catch {
      // feedback is best-effort — don't surface errors to the user
    }
  }

  return (
    <div className="flex items-center gap-0.5 border-l border-stone-200 pl-1.5 ml-0.5">
      <button
        onClick={() => submit(1)}
        title="Helpful"
        disabled={voted !== null}
        className={`p-1.5 rounded transition-colors ${
          voted === 1
            ? "text-forest-600"
            : "text-stone-400 hover:text-stone-600 hover:bg-stone-100 disabled:opacity-50"
        }`}
      >
        <svg className="w-3.5 h-3.5" fill={voted === 1 ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
        </svg>
      </button>
      <button
        onClick={() => submit(-1)}
        title="Not helpful"
        disabled={voted !== null}
        className={`p-1.5 rounded transition-colors ${
          voted === -1
            ? "text-red-500"
            : "text-stone-400 hover:text-stone-600 hover:bg-stone-100 disabled:opacity-50"
        }`}
      >
        <svg className="w-3.5 h-3.5" fill={voted === -1 ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v2a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
        </svg>
      </button>
    </div>
  );
}

interface ChatMessageProps {
  message: Message;
  question?: string;
}

export function ChatMessage({ message, question }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 mb-7 ${isUser ? "flex-row-reverse" : "flex-row"}`}>

      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5 ${
          isUser ? "bg-stone-800 text-white" : "bg-forest-800 text-white"
        }`}
      >
        {isUser ? "U" : "AI"}
      </div>

      <div className={`max-w-[78%] flex flex-col gap-1.5 ${isUser ? "items-end" : "items-start"}`}>
        <span className="text-xs text-stone-400 font-medium px-1">
          {isUser ? "You" : "Advisor"}
        </span>

        {/* Bubble */}
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "bg-stone-900 text-stone-50 rounded-tr-sm whitespace-pre-wrap"
              : "bg-white border border-stone-200 text-stone-800 rounded-tl-sm shadow-sm"
          } ${message.isStreaming ? "streaming-cursor" : ""}`}
        >
          {isUser ? (
            message.content || (message.isStreaming ? "" : "…")
          ) : (
            <div className="prose prose-sm prose-stone max-w-none prose-p:leading-relaxed prose-li:leading-relaxed prose-headings:font-semibold prose-a:text-forest-700 prose-a:no-underline hover:prose-a:underline">
              {message.content ? (
                <ReactMarkdown>{message.content}</ReactMarkdown>
              ) : message.isStreaming ? null : (
                <span>…</span>
              )}
            </div>
          )}
        </div>

        {/* Action bar — copy + share + feedback, only on completed assistant messages */}
        {!isUser && !message.isStreaming && message.content && (
          <div className="flex items-center gap-0.5 px-1">
            <CopyButton text={message.content} />
            <ShareButton question={question} />
            <FeedbackButtons question={question} />
          </div>
        )}

        {/* Citations */}
        {!isUser && message.citations && message.citations.length > 0 && !message.isStreaming && (
          <div className="flex flex-wrap gap-1.5 px-1 mt-0.5">
            <span className="text-xs text-stone-400 self-center mr-0.5">Sources:</span>
            {message.citations.map((c) => (
              <CitationChip key={c.n} citation={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
