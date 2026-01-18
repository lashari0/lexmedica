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

        return (
          <div
            key={doc.id}
            className="bg-white rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow cursor-pointer"
            onClick={handleClick}
            onMouseEnter={() => onDocumentHover?.(doc)}
            onMouseLeave={() => onDocumentHover?.(null)}
          >
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
