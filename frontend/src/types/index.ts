/**
 * Shared TypeScript types
 */

export interface Document {
  id: string;
  filename: string;
  uploaded_at: string;
  metadata?: DocumentMetadata;
  is_duplicate?: boolean;
  duplicate_of?: string;
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
  abstract?: string; // Optional: abstract of the document
  summary?: string; // Optional: summary of the document
}

export interface Citation {
  document_id: string;
  chunk_index: number;
  text: string;
  page_number?: number;
  similarity_score: number;
}

/** STEP 10: Evidence signal metadata from backend */
export interface QueryResponseMetadata {
  total_results?: number;
  sources_count?: number;
  query?: string;
  top_k_used?: number;
  sections_referenced?: number;
  single_source_evidence?: boolean;
  evidence_conflict_detected?: boolean;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
  metadata?: QueryResponseMetadata;
}

export interface QueryRequest {
  query: string;
  top_k?: number;
  document_id?: string; // STEP 5: Optional document ID for scoped queries
  scope_expanded?: boolean; // STEP 11: True when user expanded from single doc to all
}
