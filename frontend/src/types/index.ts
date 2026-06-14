export interface Citation {
  n: number;
  title: string;
  url: string;
  snippet: string;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  isStreaming?: boolean;
}
