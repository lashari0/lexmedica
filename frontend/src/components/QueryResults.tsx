'use client';

import { QueryResponse } from '@/types';
import CitationCard from './CitationCard';

interface QueryResultsProps {
  results: QueryResponse | null;
  isLoading?: boolean;
}

export default function QueryResults({ results, isLoading }: QueryResultsProps) {
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

  const confidenceColor = results.confidence > 0.7 
    ? 'text-green-600' 
    : results.confidence > 0.5 
    ? 'text-yellow-600' 
    : 'text-red-600';

  return (
    <div className="space-y-6">
      {/* Answer */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Answer</h3>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Confidence:</span>
            <span className={`text-sm font-medium ${confidenceColor}`}>
              {(results.confidence * 100).toFixed(1)}%
            </span>
          </div>
        </div>
        <div className="prose max-w-none">
          <p className="text-gray-700 whitespace-pre-wrap">{results.answer}</p>
        </div>
      </div>

      {/* Citations */}
      {results.citations.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Sources ({results.citations.length})
          </h3>
          <div className="space-y-3">
            {results.citations.map((citation, idx) => (
              <CitationCard key={idx} citation={citation} index={idx + 1} />
            ))}
          </div>
        </div>
      )}

      {results.citations.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">
            No citations found. The answer may not be based on uploaded documents.
          </p>
        </div>
      )}
    </div>
  );
}
