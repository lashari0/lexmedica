/**
 * Shared TypeScript types
 */

export interface Document {
  id: string;
  filename: string;
  uploaded_at: string;
  metadata?: DocumentMetadata;
}

export interface DocumentMetadata {
  title?: string;
  authors?: string[];
  journal?: string;
  year?: number;
  doi?: string;
}

export interface Citation {
  document_id: string;
  chunk_index: number;
  text: string;
  page_number?: number;
  similarity_score: number;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
}

export interface QueryRequest {
  query: string;
  top_k?: number;
}
