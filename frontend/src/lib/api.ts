/**
 * API client for backend communication
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type DocumentType = 
  | 'Guideline'
  | 'Systematic Review'
  | 'RCT'
  | 'Observational Study'
  | 'Other';

export interface Document {
  id: string;
  filename: string;
  uploaded_at: string;
  metadata?: {
    title?: string;
    authors?: string[];
    journal?: string;
    year?: number;
    doi?: string;
    // Evidence signaling fields (Step 2)
    authority?: string;
    document_type?: DocumentType;
    jurisdiction?: string;
    evidence_tier?: string;
    version?: string;
    superseded?: boolean;
  };
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

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  async uploadDocument(file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  async listDocuments(): Promise<Document[]> {
    const response = await this.request<{ documents: Document[] }>('/api/documents');
    return response.documents || [];
  }

  async queryDocuments(request: QueryRequest): Promise<QueryResponse> {
    return this.request<QueryResponse>('/api/queries', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async healthCheck(): Promise<{ status: string; version: string }> {
    return this.request<{ status: string; version: string }>('/api/health');
  }
}

export const apiClient = new ApiClient();
