export interface Citation {
  n: number;
  title: string;
  url: string;
  snippet: string;
  crawled_at?: string | null;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  isStreaming?: boolean;
}
