'use client';

import { useEffect } from 'react';
import { QueryResponse, Document } from '@/types';
import CitationCard from './CitationCard';

/**
 * STEP 7: Format answer text to display bullets with citation references.
 * Parses bullet points and highlights citation references.
 */
function formatAnswerWithBullets(answer: string): JSX.Element {
  // Split by lines and process each line
  const lines = answer.split('\n').filter(line => line.trim());
  
  return (
    <div className="space-y-2">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        
        // Check if line is a bullet point (starts with •, -, *, or number)
        const isBullet = /^[•\-\*]\s/.test(trimmed) || /^\d+\.\s/.test(trimmed);
        
        if (isBullet) {
          // Extract bullet marker
          const bulletMatch = trimmed.match(/^([•\-\*]|\d+\.)\s/);
          const bulletMarker = bulletMatch ? bulletMatch[1] : '•';
          
          // Extract text after bullet
          const textAfterBullet = trimmed.replace(/^[•\-\*]\s|^\d+\.\s/, '');
          
          // Find citation references like [Citation N]
          const citationPattern = /\[Citation\s+(\d+)\]/g;
          const parts: (string | JSX.Element)[] = [];
          let lastIndex = 0;
          let match;
          
          while ((match = citationPattern.exec(textAfterBullet)) !== null) {
            // Add text before citation
            if (match.index > lastIndex) {
              parts.push(textAfterBullet.substring(lastIndex, match.index));
            }
            
            // Add citation reference as highlighted element
            const citationNum = parseInt(match[1], 10);
            parts.push(
              <span
                key={`citation-${idx}-${match.index}`}
                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 ml-1"
                title={`Citation ${citationNum}`}
              >
                [{citationNum}]
              </span>
            );
            
            lastIndex = citationPattern.lastIndex;
          }
          
          // Add remaining text
          if (lastIndex < textAfterBullet.length) {
            parts.push(textAfterBullet.substring(lastIndex));
          }
          
          // If no citations found, just display the text
          if (parts.length === 0) {
            parts.push(textAfterBullet);
          }
          
          return (
            <div key={idx} className="flex items-start gap-2">
              <span className="text-gray-500 mt-0.5 flex-shrink-0">{bulletMarker}</span>
              <span className="text-gray-700 flex-1">{parts}</span>
            </div>
          );
        } else {
          // Regular paragraph text (should be minimal per STEP 7)
          return (
            <p key={idx} className="text-gray-700">
              {trimmed}
            </p>
          );
        }
      })}
    </div>
  );
}

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

      {/* Answer Panel (bounded, structured) - STEP 7: Evidence-first bullet format */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Answer</h3>
        <div className="prose max-w-none">
          {formatAnswerWithBullets(results.answer)}
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
