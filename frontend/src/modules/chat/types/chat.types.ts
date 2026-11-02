export interface ChatRequest {
  knowledge_space_id: string;
  question: string;
}

export interface ChatResponse {
  answer: string;
  intent: string | null;
  knowledge_requests: Record<string, unknown>[];
  information: Record<string, unknown>[];
  structured_results?: StructuredResult[];
}

export interface StructuredResult {
  columns: string[];
  rows: (string | number | boolean | null)[][];
  sources: { dataset_id: string; document_id: string; version: string; file_name: string; sheet: string; range: string; warnings?: string[] }[];
  truncated: boolean;
  plan: Record<string, unknown>;
  chart: { type: "bar" | "line"; x: string; y: string[]; title?: string } | null;
  row_sources?: Record<string, number | null>[];
  column_metadata?: Record<string, { data_type: string; number_format: string | null; source_column: string | null; aggregate: string | null; percentage?: boolean }>;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
}

export interface Conversation {
  id: string;
  knowledgeSpaceId: string;
  title: string;
  messages: ChatMessage[];
}
