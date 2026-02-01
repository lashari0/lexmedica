'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import DocumentList from '@/components/DocumentList';
import DocumentFilters, { FilterState } from '@/components/DocumentFilters';
import DocumentPreview from '@/components/DocumentPreview';
import LoadingSpinner from '@/components/LoadingSpinner';
import { apiClient } from '@/lib/api';
import { Document } from '@/types';
import { filterDocuments } from '@/lib/filterUtils';

export default function DocumentsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [filters, setFilters] = useState<FilterState>({
    documentTypes: [],
    yearRange: { min: null, max: null },
    authorities: [],
    jurisdictions: [],
  });

  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [hoveredDocument, setHoveredDocument] = useState<Document | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // STEP 5: Navigate to document workspace when document is clicked
  const handleDocumentClick = (document: Document) => {
    router.push(`/documents/${document.id}`);
  };

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
  });

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.pdf')) {
      setUploadError('Only PDF files are supported');
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      await apiClient.uploadDocument(file);
      // Invalidate and refetch the documents list
      await queryClient.invalidateQueries({ queryKey: ['documents'] });
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setUploadError(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  // Filter documents based on filter state
  const filteredDocuments = documents ? filterDocuments(documents, filters) : [];

  // Determine which document to show in preview (selected takes priority over hovered)
  const previewDocument = selectedDocument || hoveredDocument;

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">Document Library</h1>
              <p className="text-gray-600">
                Select a document to explore its evidence
              </p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <button
                onClick={handleUploadClick}
                disabled={isUploading}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isUploading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Uploading...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    Upload Document
                  </>
                )}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
              />
              {uploadError && (
                <p className="text-sm text-red-600">{uploadError}</p>
              )}
            </div>
          </div>
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
