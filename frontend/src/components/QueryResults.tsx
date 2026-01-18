'use client';

import { useEffect } from 'react';
import { QueryResponse, Document } from '@/types';
import CitationCard from './CitationCard';

interface QueryResultsProps {
  results: QueryResponse | null;
  isLoading?: boolean;
  document?: Document | null; // Document metadata header
  onInsufficientEvidence?: (hasInsufficientEvidence: boolean) => void; // STEP 6: Callback for insufficient evidence detection
}

export default function QueryResults({ 
  results, 
  isLoading, 
  document,
  onInsufficientEvidence,
}: QueryResultsProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-full"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  if (!results) {
    return null;
  }

  // STEP 6: Detect insufficient evidence
  // Only trigger on truly insufficient evidence: no citations OR zero confidence
  // Removed aggressive checks (< 2 citations, < 0.3 confidence) that were triggering too often
  const hasInsufficientEvidence = 
    results.citations.length === 0 || 
    (results.confidence === 0.0);

  // Notify parent component about insufficient evidence
  useEffect(() => {
    if (onInsufficientEvidence && document) {
      onInsufficientEvidence(hasInsufficientEvidence);
    }
  }, [hasInsufficientEvidence, document, onInsufficientEvidence]);

  return (
    <div className="space-y-6">
      {/* Document Metadata Header */}
      {document && (
        <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Document Evidence</h3>
          <div className="space-y-1">
            <p className="font-semibold text-gray-900">
              {document.metadata?.title || document.filename}
            </p>
            {document.metadata?.authority && (
              <p className="text-sm text-gray-600">{document.metadata.authority}</p>
            )}
            {document.metadata?.year && (
              <p className="text-xs text-gray-500">Published: {document.metadata.year}</p>
            )}
          </div>
        </div>
      )}

      {/* Answer Panel (bounded, structured) */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Answer</h3>
        <div className="prose max-w-none">
          <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
            {results.answer}
          </div>
        </div>
      </div>

      {/* Evidence Panel (citations & excerpts) */}
      {results.citations.length > 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Evidence ({results.citations.length} {results.citations.length === 1 ? 'citation' : 'citations'})
          </h3>
          <div className="space-y-4">
            {results.citations.map((citation, idx) => (
              <CitationCard key={idx} citation={citation} index={idx + 1} />
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">
            ⚠️ No supporting evidence found in this document.
          </p>
        </div>
      )}
    </div>
  );
}
