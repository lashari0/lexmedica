'use client';

import { Document } from '@/types';
import { format } from 'date-fns';

interface DocumentPreviewProps {
  document: Document | null;
}

export default function DocumentPreview({ document }: DocumentPreviewProps) {
  if (!document) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4 h-fit">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Document Preview</h2>
        <p className="text-sm text-gray-500">
          Select or hover over a document to view its details
        </p>
      </div>
    );
  }

  const metadata = document.metadata;
  const title = metadata?.title || document.filename;
  const year = metadata?.year;
  const authority = metadata?.authority || metadata?.journal;
  const documentType = metadata?.document_type;
  const jurisdiction = metadata?.jurisdiction;
  const superseded = metadata?.superseded;
  const authors = metadata?.authors;
  const abstract = metadata?.abstract || metadata?.summary; // Backend may provide this later

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 h-fit">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Document Preview</h2>

      <div className="space-y-4">
        {/* Warning Banner */}
        {superseded && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <div className="flex items-start">
              <span className="text-yellow-800 text-sm font-medium">
                ⚠️ Outdated Guideline
              </span>
            </div>
          </div>
        )}

        {/* Title */}
        <div>
          <h3 className="font-semibold text-gray-900 text-base leading-tight mb-2">
            {title}
          </h3>
        </div>

        {/* Key Metadata */}
        <div className="space-y-2 text-sm">
          {year && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500 font-medium">Year:</span>
              <span className="text-gray-900 font-semibold text-base">{year}</span>
            </div>
          )}

          {authority && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500 font-medium">Authority:</span>
              <span className="text-gray-700">{authority}</span>
            </div>
          )}

          {documentType && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500 font-medium">Type:</span>
              <span className="text-gray-700">{documentType}</span>
            </div>
          )}

          {jurisdiction && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500 font-medium">Jurisdiction:</span>
              <span className="text-gray-700">{jurisdiction}</span>
            </div>
          )}

          {authors && authors.length > 0 && (
            <div>
              <span className="text-gray-500 font-medium">Authors:</span>
              <p className="text-gray-700 mt-1">
                {authors.slice(0, 5).join(', ')}
                {authors.length > 5 && ` +${authors.length - 5} more`}
              </p>
            </div>
          )}

          <div className="flex items-center gap-2">
            <span className="text-gray-500 font-medium">Uploaded:</span>
            <span className="text-gray-700">
              {format(new Date(document.uploaded_at), 'MMM d, yyyy')}
            </span>
          </div>

          {metadata?.version && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500 font-medium">Version:</span>
              <span className="text-gray-700">{metadata.version}</span>
            </div>
          )}
        </div>

        {/* Abstract / Executive Summary */}
        {abstract && (
          <div className="pt-2 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Abstract / Summary</h4>
            <p
              className="text-sm text-gray-600 leading-relaxed"
              style={{
                display: '-webkit-box',
                WebkitLineClamp: 6,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
            >
              {abstract}
            </p>
          </div>
        )}

        {!abstract && (
          <div className="pt-2 border-t border-gray-200">
            <p className="text-xs text-gray-400 italic">
              Abstract not available for this document
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
