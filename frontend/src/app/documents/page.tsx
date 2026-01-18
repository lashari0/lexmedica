'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import DocumentList from '@/components/DocumentList';
import DocumentFilters, { FilterState } from '@/components/DocumentFilters';
import DocumentPreview from '@/components/DocumentPreview';
import LoadingSpinner from '@/components/LoadingSpinner';
import { apiClient } from '@/lib/api';
import { Document } from '@/types';
import { filterDocuments } from '@/lib/filterUtils';

export default function DocumentsPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<FilterState>({
    documentTypes: [],
    yearRange: { min: null, max: null },
    authorities: [],
    jurisdictions: [],
  });

  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [hoveredDocument, setHoveredDocument] = useState<Document | null>(null);

  // STEP 5: Navigate to document workspace when document is clicked
  const handleDocumentClick = (document: Document) => {
    router.push(`/documents/${document.id}`);
  };

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
  });

  // Filter documents based on filter state
  const filteredDocuments = documents ? filterDocuments(documents, filters) : [];

  // Determine which document to show in preview (selected takes priority over hovered)
  const previewDocument = selectedDocument || hoveredDocument;

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Document Library</h1>
          <p className="text-gray-600">
            Select a document to explore its evidence
          </p>
        </header>

        {/* Three-column layout: Left Sidebar | Main Content | Right Sidebar */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Sidebar - Filters */}
          <aside className="lg:col-span-3">
            <div className="sticky top-8">
              {documents && documents.length > 0 && (
                <DocumentFilters
                  documents={documents}
                  filters={filters}
                  onFiltersChange={setFilters}
                />
              )}
            </div>
          </aside>

          {/* Main Content - Document List */}
          <div className="lg:col-span-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              {isLoading ? (
                <LoadingSpinner size="lg" text="Loading documents..." />
              ) : (
                <>
                  {filteredDocuments.length === 0 && documents && documents.length > 0 ? (
                    <div className="text-center py-12">
                      <p className="text-gray-500">No documents match the selected filters.</p>
                      <button
                        onClick={() => setFilters({
                          documentTypes: [],
                          yearRange: { min: null, max: null },
                          authorities: [],
                          jurisdictions: [],
                        })}
                        className="mt-4 text-sm text-blue-600 hover:text-blue-800 font-medium"
                      >
                        Clear filters
                      </button>
                    </div>
                  ) : (
                    <DocumentList
                      documents={filteredDocuments}
                      onDocumentSelect={setSelectedDocument}
                      onDocumentHover={setHoveredDocument}
                      onDocumentClick={handleDocumentClick}
                    />
                  )}
                </>
              )}
            </div>
          </div>

          {/* Right Sidebar - Document Preview */}
          <aside className="lg:col-span-3">
            <div className="sticky top-8">
              <DocumentPreview document={previewDocument || null} />
            </div>
          </aside>
        </div>
      </div>
    </main>
  );
}
