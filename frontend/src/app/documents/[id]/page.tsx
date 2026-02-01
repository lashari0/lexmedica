'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import QueryInput from '@/components/QueryInput';
import QueryResults from '@/components/QueryResults';
import ScopeExpansionPrompt from '@/components/ScopeExpansionPrompt';
import LoadingSpinner from '@/components/LoadingSpinner';
import { apiClient } from '@/lib/api';
import { Document, DocumentType } from '@/types';

export default function DocumentWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const documentId = params?.id as string;

  const [query, setQuery] = useState<string>('');
  const [showExpansionPrompt, setShowExpansionPrompt] = useState<boolean>(false);
  const [scopeExpanded, setScopeExpanded] = useState<boolean>(false);
  const [expandedTypes, setExpandedTypes] = useState<DocumentType[] | null>(null);

  // Fetch all documents to find the selected one
  const { data: documents, isLoading: documentsLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
  });

  // Find the selected document
  const selectedDocument = documents?.find((doc) => doc.id === documentId) || null;

  // STEP 11: Log document_selected when user opens a document
  useEffect(() => {
    if (documentId) {
      apiClient.auditEvent('document_selected', documentId).catch(() => {
        // Non-blocking; ignore audit failures (e.g. offline)
      });
    }
  }, [documentId]);

  // Query mutation - scoped based on expansion state
  const queryMutation = useMutation({
    mutationFn: (queryText: string) => {
      // STEP 6: If scope is expanded, don't filter by document_id
      const request: { query: string; document_id?: string; scope_expanded?: boolean } = {
        query: queryText,
      };

      // Only add document_id if scope is not expanded
      if (!scopeExpanded) {
        request.document_id = documentId;
      }
      // STEP 11: Send scope_expanded so backend can audit it
      request.scope_expanded = scopeExpanded;

      return apiClient.queryDocuments(request);
    },
    onSuccess: () => {
      // Reset expansion prompt after successful query
      setShowExpansionPrompt(false);
    },
  });

  const handleQuery = (queryText: string) => {
    setQuery(queryText);
    setScopeExpanded(false); // Reset scope expansion for new query
    setExpandedTypes(null);
    queryMutation.mutate(queryText);
  };

  // STEP 6: Handle insufficient evidence detection
  const handleInsufficientEvidence = (hasInsufficientEvidence: boolean) => {
    if (hasInsufficientEvidence && !scopeExpanded && queryMutation.isSuccess) {
      setShowExpansionPrompt(true);
    }
  };

  // STEP 6: Handle scope expansion
  const handleExpandToTypes = (types: DocumentType[]) => {
    setScopeExpanded(true);
    setExpandedTypes(types);
    setShowExpansionPrompt(false);
    // Re-run query with expanded scope
    if (query) {
      queryMutation.mutate(query);
    }
  };

  const handleExpandToAll = () => {
    setScopeExpanded(true);
    setExpandedTypes(null); // null means all documents
    setShowExpansionPrompt(false);
    // Re-run query with expanded scope
    if (query) {
      queryMutation.mutate(query);
    }
  };

  const handleCancelExpansion = () => {
    setShowExpansionPrompt(false);
  };

  // Get available document types for expansion
  const availableDocumentTypes = Array.from(
    new Set(
      documents
        ?.map((doc) => doc.metadata?.document_type)
        .filter((type): type is DocumentType => type !== undefined) || []
    )
  );

  if (documentsLoading) {
    return (
      <main className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8 max-w-6xl">
          <LoadingSpinner size="lg" text="Loading document..." />
        </div>
      </main>
    );
  }

  if (!selectedDocument) {
    return (
      <main className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8 max-w-6xl">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">Document Not Found</h2>
            <p className="text-gray-600 mb-4">The requested document could not be found.</p>
            <button
              onClick={() => router.push('/documents')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Back to Documents
            </button>
          </div>
        </div>
      </main>
    );
  }

  const documentTitle = selectedDocument.metadata?.title || selectedDocument.filename;
  const documentAuthority = selectedDocument.metadata?.authority || selectedDocument.metadata?.journal;
  const documentYear = selectedDocument.metadata?.year;

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header with back button */}
        <div className="mb-6">
          <button
            onClick={() => router.push('/documents')}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium mb-4"
          >
            ← Back to Documents
          </button>
          <header className="mb-6">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Document Q&A</h1>
          </header>
        </div>

        {/* Document Metadata Header - Prominently displayed */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="border-b border-gray-200 pb-4 mb-4">
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">{documentTitle}</h2>
            {documentAuthority && (
              <p className="text-lg text-gray-600 mb-1">{documentAuthority}</p>
            )}
            {documentYear && (
              <p className="text-sm text-gray-500">Published: {documentYear}</p>
            )}
          </div>
          {/* STEP 5: Required UI Copy */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800 font-medium">
              Answers are limited to this document unless scope is expanded.
            </p>
          </div>
        </div>

        {/* STEP 12: Explicit context — no query without document context */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Ask this document</h3>
          <p className="text-sm text-gray-500 mb-4">
            Context: {scopeExpanded ? 'All documents (scope expanded)' : documentTitle}
          </p>
          <QueryInput
            onSubmit={handleQuery}
            isLoading={queryMutation.isPending}
            placeholder={scopeExpanded ? 'Ask across all documents...' : 'Ask this document...'}
          />
        </div>

        {/* STEP 12: Scope changes explicit — banner when scope expanded */}
        {scopeExpanded && (
          <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4" role="status" aria-live="polite">
            <p className="text-sm font-medium text-blue-900">
              Scope expanded: searching across all documents.
            </p>
            <p className="text-xs text-blue-700 mt-1">
              Answers may cite any uploaded document. To limit to one document again, ask a new question.
            </p>
          </div>
        )}

        {/* Loading State */}
        {queryMutation.isPending && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <LoadingSpinner size="lg" text="Exploring evidence..." />
          </div>
        )}

        {/* STEP 6: Scope Expansion Prompt */}
        {showExpansionPrompt && selectedDocument && (
          <div className="mb-6">
            <ScopeExpansionPrompt
              query={query}
              currentDocumentTitle={selectedDocument.metadata?.title || selectedDocument.filename}
              onCancel={handleCancelExpansion}
              onExpandToTypes={handleExpandToTypes}
              onExpandToAll={handleExpandToAll}
              availableDocumentTypes={availableDocumentTypes}
            />
          </div>
        )}

        {/* Results Section - Hide when expansion prompt is showing to avoid redundancy */}
        {queryMutation.isSuccess && queryMutation.data && !showExpansionPrompt && (
          <QueryResults
            results={queryMutation.data}
            document={scopeExpanded ? null : selectedDocument} // Hide document header if expanded
            onInsufficientEvidence={handleInsufficientEvidence}
          />
        )}

        {/* Error State */}
        {queryMutation.isError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">
              Error: {queryMutation.error instanceof Error ? queryMutation.error.message : 'Unknown error'}
            </p>
          </div>
        )}
      </div>
    </main>
  );
}
