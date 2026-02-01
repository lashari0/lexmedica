'use client';

import { Citation } from '@/types';

interface CitationCardProps {
  citation: Citation;
  index: number;
}

/** STEP 10: Non-numeric relevance tier (no confidence %) */
function relevanceTier(score: number): 'High' | 'Medium' | 'Low' {
  if (score > 0.7) return 'High';
  if (score > 0.5) return 'Medium';
  return 'Low';
}

export default function CitationCard({ citation, index }: CitationCardProps) {
  const tier = relevanceTier(citation.similarity_score);
  const tierColor =
    tier === 'High'
      ? 'bg-green-100 text-green-800'
      : tier === 'Medium'
        ? 'bg-yellow-100 text-yellow-800'
        : 'bg-gray-100 text-gray-800';

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-500">#{index}</span>
          <span className="text-sm font-semibold text-gray-900">
            Document: {citation.document_id}
          </span>
          {citation.page_number && (
            <span className="text-xs text-gray-500">
              Page {citation.page_number}
            </span>
          )}
        </div>
        <span className={`text-xs px-2 py-1 rounded ${tierColor}`}>
          {tier} relevance
        </span>
      </div>
      <p className="text-sm text-gray-700 line-clamp-3">
        {citation.text?.trim() || 'No excerpt available.'}
      </p>
      <div className="mt-2 text-xs text-gray-500">
        Chunk {citation.chunk_index}
      </div>
    </div>
  );
}
