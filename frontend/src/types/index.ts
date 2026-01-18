/**
 * Shared TypeScript types
 */

export interface Document {
  id: string;
  filename: string;
  uploaded_at: string;
  metadata?: DocumentMetadata;
}

export type DocumentType = 
  | 'Guideline'
  | 'Systematic Review'
  | 'RCT'
  | 'Observational Study'
  | 'Other';

export interface DocumentMetadata {
  title?: string;
  authors?: string[];
  journal?: string;
  year?: number;
  doi?: string;
  // Evidence signaling fields (Step 2)
  authority?: string; // e.g., WHO, NEJM, FDA
  document_type?: DocumentType;
  jurisdiction?: string; // e.g., US, EU, Global
  evidence_tier?: string; // Optional: visual indicator
  version?: string; // Optional: version number
  superseded?: boolean; // Optional: outdated warning
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
  document_id?: string; // STEP 5: Optional document ID for scoped queries
}
