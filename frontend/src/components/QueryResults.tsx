'use client';

import { useEffect, useCallback } from 'react';
import { QueryResponse, Document } from '@/types';
import { Citation } from '@/types';
import CitationCard from './CitationCard';

/** Parse answer for citation numbers [Citation N] or [N] in order of first appearance. */
function getCitedCitationNumbers(answer: string): number[] {
  const seen = new Set<number>();
  const order: number[] = [];
  const re = /\[Citation\s*(\d+)\]|\[(\d+)\]/g;
  let m;
  while ((m = re.exec(answer)) !== null) {
    const num = parseInt(m[1] ?? m[2], 10);
    if (!seen.has(num)) {
      seen.add(num);
      order.push(num);
    }
  }
  return order;
}

/**
 * STEP 7: Format answer text to display bullets with citation references.
 * Optionally makes [N] clickable to scroll to the corresponding evidence card.
 */
function formatAnswerWithBullets(
  answer: string,
  onCitationClick?: (citationNum: number) => void
): JSX.Element {
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
          
          // Find citation references like [Citation N] or [N]
          const citationPattern = /\[Citation\s*(\d+)\]|\[(\d+)\]/g;
          const parts: (string | JSX.Element)[] = [];
          let lastIndex = 0;
          let match;
          
          while ((match = citationPattern.exec(textAfterBullet)) !== null) {
            // Add text before citation
            if (match.index > lastIndex) {
              parts.push(textAfterBullet.substring(lastIndex, match.index));
            }
            
            // Add citation reference as highlighted element
            const citationNum = parseInt(match[1] ?? match[2], 10);
            const isClickable = !!onCitationClick;
            parts.push(
              isClickable ? (
                <button
                  key={`citation-${idx}-${match.index}`}
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onCitationClick(citationNum);
                  }}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 ml-1 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
                  title={`Jump to evidence ${citationNum}`}
                >
                  [{citationNum}]
                </button>
              ) : (
                <span
                  key={`citation-${idx}-${match.index}`}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 ml-1"
                  title={`Citation ${citationNum}`}
                >
                  [{citationNum}]
                </span>
              )
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

  // Only show citations that are referenced in the answer ([1], [2], etc.), in that order
  const citedNumbers = getCitedCitationNumbers(results.answer);
  const displayedCitations: { citation: Citation; displayNum: number }[] =
    citedNumbers.length > 0
      ? citedNumbers
          .filter((n) => n >= 1 && n <= results.citations.length)
          .map((n) => ({ citation: results.citations[n - 1], displayNum: n }))
      : results.citations.map((c, i) => ({ citation: c, displayNum: i + 1 }));

  const scrollToCitation = useCallback((citationNum: number) => {
    const id = `citation-${citationNum}`;
    const doScroll = () => {
      if (typeof window === 'undefined') return;
      const el = window.document.getElementById(id);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
      }
    };
    requestAnimationFrame(doScroll);
    setTimeout(doScroll, 100);
  }, []);

  // STEP 10: Evidence signals (non-numeric confidence)
  const sectionsReferenced =
    results.metadata?.sections_referenced ??
    (citedNumbers.length > 0 ? citedNumbers.length : displayedCitations.length);
  const hasEvidence = results.citations.length > 0;
  const showSignalsStrip = hasEvidence && (sectionsReferenced > 0 || results.metadata?.single_source_evidence || results.metadata?.evidence_conflict_detected);

  // STEP 12: Refusal = no citations or explicit refusal phrase (visible, non-punitive)
  const isRefusal =
    results.citations.length === 0 ||
    results.answer.toLowerCase().includes('insufficient evidence');

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

      {/* STEP 10: Evidence signals strip (non-numeric) */}
      {showSignalsStrip && (
        <div className="flex flex-wrap items-center gap-3 text-sm">
          {sectionsReferenced > 0 && (
            <span className="text-gray-600">
              {sectionsReferenced} section{sectionsReferenced !== 1 ? 's' : ''} referenced
            </span>
          )}
          {results.metadata?.single_source_evidence && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-md bg-gray-100 text-gray-700 font-medium">
              Single-source evidence
            </span>
          )}
          {results.metadata?.evidence_conflict_detected && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-md bg-amber-100 text-amber-800 font-medium">
              Evidence conflict detected
            </span>
          )}
        </div>
      )}

      {/* STEP 12: Refusal visible and non-punitive — neutral informational block */}
      {isRefusal && (
        <div
          className="rounded-lg border border-slate-200 bg-slate-50 p-4"
          role="status"
          aria-live="polite"
        >
          <h4 className="text-sm font-semibold text-slate-800">Refusal — insufficient evidence</h4>
          <p className="text-sm text-slate-600 mt-1">
            The system did not find enough evidence in the selected context to answer. This is expected behavior, not an error.
          </p>
        </div>
      )}

      {/* STEP 12: Evidence visually dominant — Evidence panel above Answer */}
      {/* Evidence Panel: only citations referenced in the answer, [1] and [2] map to cards */}
      {displayedCitations.length > 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Evidence ({displayedCitations.length} {displayedCitations.length === 1 ? 'citation' : 'citations'} cited in answer)
          </h3>
          <div className="space-y-4">
            {displayedCitations.map(({ citation, displayNum }) => (
              <div
                key={displayNum}
                id={`citation-${displayNum}`}
                className="scroll-mt-4"
                tabIndex={-1}
              >
                <CitationCard citation={citation} index={displayNum} />
              </div>
            ))}
          </div>
        </div>
      ) : results.citations.length > 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Evidence ({results.citations.length} {results.citations.length === 1 ? 'citation' : 'citations'})
          </h3>
          <div className="space-y-4">
            {results.citations.map((citation, idx) => (
              <div
                key={idx}
                id={`citation-${idx + 1}`}
                className="scroll-mt-4"
                tabIndex={-1}
              >
                <CitationCard citation={citation} index={idx + 1} />
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Answer Panel (bounded, structured) - STEP 7: below Evidence per STEP 12 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Answer</h3>
        <div className="prose max-w-none">
          {formatAnswerWithBullets(results.answer, scrollToCitation)}
        </div>
      </div>
    </div>
  );
}
