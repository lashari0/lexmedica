import { Document } from '@/types';
import { FilterState } from '@/components/DocumentFilters';

/**
 * Filter documents based on filter state
 */
export function filterDocuments(documents: Document[], filters: FilterState): Document[] {
  return documents.filter((doc) => {
    // Document Type filter
    if (filters.documentTypes.length > 0) {
      const docType = doc.metadata?.document_type;
      if (!docType || !filters.documentTypes.includes(docType)) {
        return false;
      }
    }

    // Year Range filter
    const docYear = doc.metadata?.year;
    if (docYear !== undefined) {
      if (filters.yearRange.min !== null && docYear < filters.yearRange.min) {
        return false;
      }
      if (filters.yearRange.max !== null && docYear > filters.yearRange.max) {
        return false;
      }
    }

    // Authority/Source filter
    if (filters.authorities.length > 0) {
      const docAuthority = doc.metadata?.authority || doc.metadata?.journal;
      if (!docAuthority || !filters.authorities.includes(docAuthority)) {
        return false;
      }
    }

    // Jurisdiction filter
    if (filters.jurisdictions.length > 0) {
      const docJurisdiction = doc.metadata?.jurisdiction;
      if (!docJurisdiction || !filters.jurisdictions.includes(docJurisdiction)) {
        return false;
      }
    }

    return true;
  });
}
