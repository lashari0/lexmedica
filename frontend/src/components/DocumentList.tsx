'use client';

import { Document, DocumentType } from '@/types';
import { format } from 'date-fns';

interface DocumentListProps {
  documents: Document[];
  onDelete?: (documentId: string) => void;
  isLoading?: boolean;
  onDocumentSelect?: (document: Document) => void;
  onDocumentHover?: (document: Document | null) => void;
  onDocumentClick?: (document: Document) => void; // For navigation to workspace
}

// Helper function to get document type badge color (subtle, not decorative)
function getDocumentTypeStyle(type?: DocumentType) {
  switch (type) {
    case 'Guideline':
      return 'bg-gray-50 border-gray-300 text-gray-800';
    case 'Systematic Review':
      return 'bg-gray-50 border-gray-300 text-gray-800';
    case 'RCT':
      return 'bg-gray-50 border-gray-300 text-gray-800';
    case 'Observational Study':
      return 'bg-gray-50 border-gray-300 text-gray-800';
    default:
      return 'bg-gray-50 border-gray-300 text-gray-800';
  }
}

// Truncate title to max 2 lines
function truncateTitle(title: string, maxLength: number = 120): string {
  if (title.length <= maxLength) return title;
  return title.slice(0, maxLength) + '...';
}

export default function DocumentList({ 
  documents, 
  isLoading, 
  onDocumentSelect, 
  onDocumentHover,
  onDocumentClick,
  onDelete,
}: DocumentListProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse bg-gray-200 h-32 rounded-lg"></div>
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
    <div className="space-y-4">
      {documents.map((doc) => {
        const title = doc.metadata?.title || doc.filename;
        const truncatedTitle = truncateTitle(title);
        const year = doc.metadata?.year;
        const authority = doc.metadata?.authority || doc.metadata?.journal;
        const documentType = doc.metadata?.document_type;
        const jurisdiction = doc.metadata?.jurisdiction;
        const superseded = doc.metadata?.superseded;

        const handleClick = () => {
          onDocumentSelect?.(doc);
          onDocumentClick?.(doc);
        };

        const handleDeleteClick = (e: React.MouseEvent) => {
          e.stopPropagation();
          onDelete?.(doc.id);
        };

        return (
          <div
            key={doc.id}
            className="bg-white rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow cursor-pointer relative group"
            onClick={handleClick}
            onMouseEnter={() => onDocumentHover?.(doc)}
            onMouseLeave={() => onDocumentHover?.(null)}
          >
            {/* Delete button */}
            {onDelete && (
              <button
                type="button"
                onClick={handleDeleteClick}
                className="absolute top-4 right-4 p-1.5 rounded-md text-gray-400 hover:text-red-600 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1 opacity-0 group-hover:opacity-100 transition-opacity"
                title="Delete document"
                aria-label="Delete document"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            )}
            {/* Superseded Warning Badge */}
            {superseded && (
              <div className="mb-3">
                <span className="inline-flex items-center px-3 py-1 rounded text-xs font-medium bg-yellow-50 border border-yellow-200 text-yellow-800">
                  ⚠️ Outdated Guideline
                </span>
              </div>
            )}

            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                {/* Title (max 2 lines) */}
                <h3 
                  className="font-semibold text-gray-900 text-base leading-tight mb-3"
                  style={{
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                  }}
                >
                  {truncatedTitle}
                </h3>

                {/* Evidence Signaling Metadata Row */}
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-3 text-sm">
                    {/* Authority/Source */}
                    {authority && (
                      <div className="flex items-center gap-1.5">
                        <span className="text-gray-600 font-medium">{authority}</span>
                      </div>
                    )}

                    {/* Publication Year (large, visually distinct) */}
                    {year && (
                      <div className="flex items-center">
                        <span className="text-lg font-bold text-gray-900">{year}</span>
                      </div>
                    )}

                    {/* Document Type Badge */}
                    {documentType && (
                      <div className="flex items-center">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium border ${getDocumentTypeStyle(documentType)}`}
                        >
                          {documentType}
                        </span>
                      </div>
                    )}

                    {/* Jurisdiction */}
                    {jurisdiction && (
                      <div className="flex items-center gap-1.5">
                        <span className="text-gray-500 text-xs">Jurisdiction:</span>
                        <span className="text-gray-700 font-medium text-xs">{jurisdiction}</span>
                      </div>
                    )}
                  </div>

                  {/* Secondary Metadata (smaller, less prominent) */}
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500 pt-1">
                    <span>
                      Uploaded: {format(new Date(doc.uploaded_at), 'MMM d, yyyy')}
                    </span>
                    {doc.metadata?.authors && doc.metadata.authors.length > 0 && (
                      <span>
                        {doc.metadata.authors.slice(0, 2).join(', ')}
                        {doc.metadata.authors.length > 2 && ` +${doc.metadata.authors.length - 2} more`}
                      </span>
                    )}
                    {doc.metadata?.version && (
                      <span>Version: {doc.metadata.version}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
