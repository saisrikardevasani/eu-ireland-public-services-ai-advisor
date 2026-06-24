/**
 * Streams a chat response from the backend using the Fetch API.
 *
 * Why not use EventSource?
 * The built-in EventSource API only supports GET requests. Our chat endpoint
 * uses POST (to send the question in the request body), so we use fetch()
 * and read the response body as a stream ourselves.
 */

import type { Citation } from "@/types";

interface StreamCallbacks {
  onToken: (token: string) => void;
  onCitations: (citations: Citation[]) => void;
  onDone: () => void;
  onError: (message: string) => void;
}

export async function streamChat(
  question: string,
  callbacks: StreamCallbacks,
  conversationId?: string,
): Promise<void> {
  const response = await fetch("/api/v1/chat/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: question, conversation_id: conversationId ?? null }),
  });

  if (!response.ok) {
    const msg = response.status === 503
      ? "The backend is still waking up. Wait ~30 seconds and try again."
      : response.status === 429
      ? "Rate limit reached. Please wait a moment before sending another message."
      : `Server error: ${response.status}`;
    callbacks.onError(msg);
    return;
  }

  if (!response.body) {
    callbacks.onError("No response body received");
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    // Decode the incoming bytes and append to buffer
    buffer += decoder.decode(value, { stream: true });

    // SSE frames are separated by \n\n — process complete frames
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? ""; // keep the incomplete last frame

    for (const frame of frames) {
      if (!frame.trim()) continue;

      // Parse event name and data from the frame
      const lines = frame.split("\n");
      let event = "message";
      let dataStr = "";

      for (const line of lines) {
        if (line.startsWith("event: ")) event = line.slice(7);
        if (line.startsWith("data: ")) dataStr = line.slice(6);
      }

      if (!dataStr) continue;

      try {
        const data = JSON.parse(dataStr);

        switch (event) {
          case "token":
            callbacks.onToken(data.text ?? "");
            break;
          case "citations":
            callbacks.onCitations(data.citations ?? []);
            break;
          case "done":
            callbacks.onDone();
            break;
          case "error":
            callbacks.onError(data.message ?? "Unknown error");
            break;
        }
      } catch {
        // Non-JSON frame (e.g. [DONE] sentinel) — skip
      }
    }
  }
}
