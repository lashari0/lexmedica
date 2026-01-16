'use client';

import { useQuery } from '@tanstack/react-query';
import DocumentList from '@/components/DocumentList';
import LoadingSpinner from '@/components/LoadingSpinner';
import { apiClient } from '@/lib/api';

export default function DocumentsPage() {
  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
  });

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Document Library</h1>
          <p className="text-gray-600">
            View and manage your uploaded medical research documents
          </p>
        </header>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          {isLoading ? (
            <LoadingSpinner size="lg" text="Loading documents..." />
          ) : (
            <DocumentList documents={documents || []} />
          )}
        </div>
      </div>
    </main>
  );
}
