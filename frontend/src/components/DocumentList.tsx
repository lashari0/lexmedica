'use client';

import { Document } from '@/types';
import { format } from 'date-fns';

interface DocumentListProps {
  documents: Document[];
  onDelete?: (documentId: string) => void;
  isLoading?: boolean;
}

export default function DocumentList({ documents, isLoading }: DocumentListProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse bg-gray-200 h-20 rounded"></div>
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No documents uploaded yet.</p>
        <p className="text-sm text-gray-400 mt-2">Upload a PDF to get started.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {documents.map((doc) => (
        <div
          key={doc.id}
          className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h4 className="font-medium text-gray-900">{doc.filename}</h4>
              {doc.metadata?.title && (
                <p className="text-sm text-gray-600 mt-1">{doc.metadata.title}</p>
              )}
              <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                <span>
                  Uploaded: {format(new Date(doc.uploaded_at), 'MMM d, yyyy')}
                </span>
                {doc.metadata?.authors && doc.metadata.authors.length > 0 && (
                  <span>
                    Authors: {doc.metadata.authors.slice(0, 2).join(', ')}
                    {doc.metadata.authors.length > 2 && '...'}
                  </span>
                )}
              </div>
            </div>
            <div className="ml-4">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Processed
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
