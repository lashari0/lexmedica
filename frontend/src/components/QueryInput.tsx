'use client';

import { useState, FormEvent } from 'react';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export default function QueryInput({ onSubmit, isLoading = false, placeholder = "Ask this document..." }: QueryInputProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
      setQuery('');
    }
  };

  const exampleQueries = [
    "What are the main findings?",
    "Summarize the methodology",
    "What are the conclusions?",
  ];

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            disabled={isLoading}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Exploring...' : 'Explore'}
          </button>
        </div>
      </form>
      
      {exampleQueries.length > 0 && (
        <div className="mt-4">
          <p className="text-sm text-gray-500 mb-2">Explore evidence:</p>
          <div className="flex flex-wrap gap-2">
            {exampleQueries.map((example, idx) => (
              <button
                key={idx}
                onClick={() => setQuery(example)}
                disabled={isLoading}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
