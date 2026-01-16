'use client';

import { Citation } from '@/types';

interface CitationCardProps {
  citation: Citation;
  index: number;
}

export default function CitationCard({ citation, index }: CitationCardProps) {
  const similarityColor = citation.similarity_score > 0.7 
    ? 'bg-green-100 text-green-800' 
    : citation.similarity_score > 0.5 
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
        <span className={`text-xs px-2 py-1 rounded ${similarityColor}`}>
          {(citation.similarity_score * 100).toFixed(1)}% match
        </span>
      </div>
      <p className="text-sm text-gray-700 line-clamp-3">
        {citation.text}
      </p>
      <div className="mt-2 text-xs text-gray-500">
        Chunk {citation.chunk_index}
      </div>
    </div>
  );
}
