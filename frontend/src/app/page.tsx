'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import DocumentUpload from '@/components/DocumentUpload';
import QueryInput from '@/components/QueryInput';
import QueryResults from '@/components/QueryResults';
import LoadingSpinner from '@/components/LoadingSpinner';
import { apiClient, Document, QueryResponse } from '@/lib/api';

export default function Home() {
  const [query, setQuery] = useState<string>('');
  const queryClient = useQueryClient();

  // Fetch documents
  const { data: documents, isLoading: documentsLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
  });

  // Query mutation
  const queryMutation = useMutation({
    mutationFn: (queryText: string) => apiClient.queryDocuments({ query: queryText }),
    onSuccess: () => {
      // Optionally refetch documents after query
    },
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => apiClient.uploadDocument(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const handleQuery = (queryText: string) => {
    setQuery(queryText);
    queryMutation.mutate(queryText);
  };

  const handleUploadSuccess = (document: Document) => {
    console.log('Document uploaded:', document);
    // Documents will be refetched automatically
  };

  const handleUploadError = (error: string) => {
    alert(`Upload failed: ${error}`);
  };

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Medical Research Knowledge Assistant
          </h1>
          <p className="text-gray-600">
            Upload medical research papers and ask questions powered by AI
          </p>
        </header>

        {/* Document Upload Section */}
        <section className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">Upload Documents</h2>
          <DocumentUpload
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
          />
        </section>

        {/* Documents List */}
        {documents && documents.length > 0 && (
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Uploaded Documents ({documents.length})
            </h2>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              {documentsLoading ? (
                <LoadingSpinner text="Loading documents..." />
              ) : (
                <div className="space-y-3">
                  {documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div>
                        <p className="font-medium text-gray-900">{doc.filename}</p>
                        <p className="text-sm text-gray-500">
                          Uploaded: {new Date(doc.uploaded_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}

        {/* Query Section */}
        <section className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">Ask a Question</h2>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <QueryInput
              onSubmit={handleQuery}
              isLoading={queryMutation.isPending}
            />
          </div>
        </section>

        {/* Results Section */}
        {queryMutation.isPending && (
          <section className="mb-8">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <LoadingSpinner size="lg" text="Searching documents and generating answer..." />
            </div>
          </section>
        )}

        {queryMutation.isSuccess && queryMutation.data && (
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Results</h2>
            <QueryResults results={queryMutation.data} />
          </section>
        )}

        {queryMutation.isError && (
          <section className="mb-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">
                Error: {queryMutation.error instanceof Error ? queryMutation.error.message : 'Unknown error'}
              </p>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
