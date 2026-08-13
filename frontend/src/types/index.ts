export type DocumentStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export interface DocumentItem {
  id: string;
  filename: string;

  source_type: string;
  source_uri?: string;
  title?: string;
  mime_type?: string;
  file_size?: number;
  status: DocumentStatus;
  chunk_count: number;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface IngestJobStatus {
  job_id: string;
  document_id: string;
  status: DocumentStatus;
  error?: string;
  started_at?: string;
  completed_at?: string;
}

export interface Citation {
  document: string;
  source_type: string;
  chunk_id: string;
  score: number;
  page?: number;
  slide?: number;
  url?: string;
  section?: string;
}

export interface RetrievalDebugInfo {
  original_query: string;
  rewritten_query: string;
  expanded_queries: string[];
  retrieved_candidates_count: number;
  reranked_candidates_count: number;
  selected_context_count: number;
  context_token_count: number;
  intent: string;
  extracted_keywords: string[];
}

export interface QueryResponsePayload {
  session_id: string;
  query: string;
  rewritten_query: string;
  answer: string;
  sources: Citation[];
  retrieval_debug: RetrievalDebugInfo;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: Citation[];
  created_at: string;
  isStreaming?: boolean;
  retrieval_debug?: RetrievalDebugInfo;
}
