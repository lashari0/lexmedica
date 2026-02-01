'use client';

import { DocumentType } from '@/types';
import { Document } from '@/types';

export interface FilterState {
  searchQuery: string;
  duplicatesOnly: boolean;
  uploadedDateRange: { from: string | null; to: string | null };
  documentTypes: DocumentType[];
  yearRange: { min: number | null; max: number | null };
  authorities: string[];
  jurisdictions: string[];
}

interface DocumentFiltersProps {
  documents: Document[];
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
}

export default function DocumentFilters({ documents, filters, onFiltersChange }: DocumentFiltersProps) {
  // Extract unique filter options from documents
  const allDocumentTypes = Array.from(
    new Set(
      documents
        .map((doc) => doc.metadata?.document_type)
        .filter((type): type is DocumentType => type !== undefined)
    )
  );

  const allAuthorities = Array.from(
    new Set(
      documents
        .map((doc) => doc.metadata?.authority || doc.metadata?.journal)
        .filter((auth): auth is string => auth !== undefined)
    )
  ).sort();

  const allJurisdictions = Array.from(
    new Set(
      documents
        .map((doc) => doc.metadata?.jurisdiction)
        .filter((jur): jur is string => jur !== undefined)
    )
  ).sort();

  const allYears = documents
    .map((doc) => doc.metadata?.year)
    .filter((year): year is number => year !== undefined)
    .sort((a, b) => a - b);

  const minYear = allYears.length > 0 ? Math.min(...allYears) : null;
  const maxYear = allYears.length > 0 ? Math.max(...allYears) : null;

  const handleDocumentTypeToggle = (type: DocumentType) => {
    const newTypes = filters.documentTypes.includes(type)
      ? filters.documentTypes.filter((t) => t !== type)
      : [...filters.documentTypes, type];
    onFiltersChange({ ...filters, documentTypes: newTypes });
  };

  const handleAuthorityToggle = (authority: string) => {
    const newAuthorities = filters.authorities.includes(authority)
      ? filters.authorities.filter((a) => a !== authority)
      : [...filters.authorities, authority];
    onFiltersChange({ ...filters, authorities: newAuthorities });
  };

  const handleJurisdictionToggle = (jurisdiction: string) => {
    const newJurisdictions = filters.jurisdictions.includes(jurisdiction)
      ? filters.jurisdictions.filter((j) => j !== jurisdiction)
      : [...filters.jurisdictions, jurisdiction];
    onFiltersChange({ ...filters, jurisdictions: newJurisdictions });
  };

  const handleYearRangeChange = (field: 'min' | 'max', value: string) => {
    const numValue = value === '' ? null : parseInt(value, 10);
    onFiltersChange({
      ...filters,
      yearRange: {
        ...filters.yearRange,
        [field]: numValue,
      },
    });
  };

  const handleUploadedDateChange = (field: 'from' | 'to', value: string) => {
    onFiltersChange({
      ...filters,
      uploadedDateRange: {
        ...filters.uploadedDateRange,
        [field]: value === '' ? null : value,
      },
    });
  };

  const clearFilters = () => {
    onFiltersChange({
      searchQuery: '',
      duplicatesOnly: false,
      uploadedDateRange: { from: null, to: null },
      documentTypes: [],
      yearRange: { min: null, max: null },
      authorities: [],
      jurisdictions: [],
    });
  };

  const hasActiveFilters =
    (filters.searchQuery?.trim() ?? '') !== '' ||
    filters.duplicatesOnly ||
    (filters.uploadedDateRange?.from ?? null) !== null ||
    (filters.uploadedDateRange?.to ?? null) !== null ||
    filters.documentTypes.length > 0 ||
    filters.authorities.length > 0 ||
    filters.jurisdictions.length > 0 ||
    filters.yearRange.min !== null ||
    filters.yearRange.max !== null;

  const handleSearchChange = (value: string) => {
    onFiltersChange({ ...filters, searchQuery: value });
  };

  const handleDuplicatesOnlyToggle = () => {
    onFiltersChange({ ...filters, duplicatesOnly: !filters.duplicatesOnly });
  };

  const hasDuplicates = documents.some((d) => d.is_duplicate);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 h-fit">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Clear All
          </button>
        )}
      </div>

      <div className="space-y-6">
        {/* Search by filename or title */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Search</h3>
          <input
            type="text"
            value={filters.searchQuery ?? ''}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="Filename or title..."
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Duplicates only (when any duplicates exist) */}
        {hasDuplicates && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Duplicates</h3>
            <label className="flex items-center cursor-pointer hover:bg-gray-50 p-2 rounded-md">
              <input
                type="checkbox"
                checked={filters.duplicatesOnly}
                onChange={handleDuplicatesOnlyToggle}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">Show duplicates only</span>
            </label>
          </div>
        )}

        {/* Uploaded date range */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Uploaded date</h3>
          <div className="grid grid-cols-1 gap-2">
            <div>
              <label className="block text-xs text-gray-500 mb-1">From</label>
              <input
                type="date"
                value={filters.uploadedDateRange?.from ?? ''}
                onChange={(e) => handleUploadedDateChange('from', e.target.value)}
                className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">To</label>
              <input
                type="date"
                value={filters.uploadedDateRange?.to ?? ''}
                onChange={(e) => handleUploadedDateChange('to', e.target.value)}
                className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Document Type Filter */}
        {allDocumentTypes.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Document Type</h3>
            <div className="space-y-2">
              {allDocumentTypes.map((type) => (
                <label
                  key={type}
                  className="flex items-center cursor-pointer hover:bg-gray-50 p-2 rounded-md"
                >
                  <input
                    type="checkbox"
                    checked={filters.documentTypes.includes(type)}
                    onChange={() => handleDocumentTypeToggle(type)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">{type}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Year Range Filter */}
        {minYear !== null && maxYear !== null && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Publication Year</h3>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Min</label>
                <input
                  type="number"
                  min={minYear}
                  max={maxYear}
                  value={filters.yearRange.min ?? ''}
                  onChange={(e) => handleYearRangeChange('min', e.target.value)}
                  placeholder={minYear.toString()}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Max</label>
                <input
                  type="number"
                  min={minYear}
                  max={maxYear}
                  value={filters.yearRange.max ?? ''}
                  onChange={(e) => handleYearRangeChange('max', e.target.value)}
                  placeholder={maxYear.toString()}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        )}

        {/* Authority/Source Filter */}
        {allAuthorities.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Authority / Source</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {allAuthorities.map((authority) => (
                <label
                  key={authority}
                  className="flex items-center cursor-pointer hover:bg-gray-50 p-2 rounded-md"
                >
                  <input
                    type="checkbox"
                    checked={filters.authorities.includes(authority)}
                    onChange={() => handleAuthorityToggle(authority)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 truncate">{authority}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Jurisdiction Filter */}
        {allJurisdictions.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Jurisdiction</h3>
            <div className="space-y-2">
              {allJurisdictions.map((jurisdiction) => (
                <label
                  key={jurisdiction}
                  className="flex items-center cursor-pointer hover:bg-gray-50 p-2 rounded-md"
                >
                  <input
                    type="checkbox"
                    checked={filters.jurisdictions.includes(jurisdiction)}
                    onChange={() => handleJurisdictionToggle(jurisdiction)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">{jurisdiction}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
