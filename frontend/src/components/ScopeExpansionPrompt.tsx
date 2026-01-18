'use client';

import { useState } from 'react';
import { DocumentType } from '@/types';

interface ScopeExpansionPromptProps {
  query: string;
  currentDocumentTitle: string;
  onCancel: () => void;
  onExpandToTypes: (types: DocumentType[]) => void;
  onExpandToAll: () => void;
  availableDocumentTypes: DocumentType[];
}

export default function ScopeExpansionPrompt({
  query,
  currentDocumentTitle,
  onCancel,
  onExpandToTypes,
  onExpandToAll,
  availableDocumentTypes,
}: ScopeExpansionPromptProps) {
  const [selectedTypes, setSelectedTypes] = useState<DocumentType[]>([]);

  const handleTypeToggle = (type: DocumentType) => {
    setSelectedTypes((prev) =>
      prev.includes(type)
        ? prev.filter((t) => t !== type)
        : [...prev, type]
    );
  };

  const handleExpandToTypes = () => {
    if (selectedTypes.length > 0) {
      onExpandToTypes(selectedTypes);
    }
  };

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-blue-900 mb-2">
          Scope Expansion Required
        </h3>
        <p className="text-blue-800 mb-1">
          This question requires evidence from additional documents. Expand scope?
        </p>
        <p className="text-sm text-blue-700 italic">
          Current scope: {currentDocumentTitle}
        </p>
      </div>

      <div className="space-y-3">
        {/* Expand to Selected Document Types */}
        {availableDocumentTypes.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-blue-900 mb-2">
              Expand to selected document types:
            </label>
            <div className="space-y-2 mb-3">
              {availableDocumentTypes.map((type) => (
                <label
                  key={type}
                  className="flex items-center cursor-pointer hover:bg-blue-100 p-2 rounded"
                >
                  <input
                    type="checkbox"
                    checked={selectedTypes.includes(type)}
                    onChange={() => handleTypeToggle(type)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-blue-800">{type}</span>
                </label>
              ))}
            </div>
            <button
              onClick={handleExpandToTypes}
              disabled={selectedTypes.length === 0}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm font-medium"
            >
              Expand to Selected Types
            </button>
          </div>
        )}

        {/* Expand to All Documents */}
        <div className="pt-2 border-t border-blue-200">
          <button
            onClick={onExpandToAll}
            className="px-4 py-2 bg-blue-700 text-white rounded-lg hover:bg-blue-800 text-sm font-medium"
          >
            Expand to All Documents (Advanced)
          </button>
        </div>

        {/* Cancel */}
        <div>
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-50 text-sm font-medium"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
