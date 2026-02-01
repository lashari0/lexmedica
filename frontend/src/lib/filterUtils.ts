import { Document } from '@/types';
import { FilterState } from '@/components/DocumentFilters';

/**
 * Filter documents based on filter state
 */
export function filterDocuments(documents: Document[], filters: FilterState): Document[] {
  return documents.filter((doc) => {
    // Search filter (filename or title)
    const query = (filters.searchQuery ?? '').trim().toLowerCase();
    if (query) {
      const filename = (doc.filename ?? '').toLowerCase();
      const title = (doc.metadata?.title ?? '').toLowerCase();
      if (!filename.includes(query) && !title.includes(query)) {
        return false;
      }
    }

    // Duplicates only
    if (filters.duplicatesOnly && !doc.is_duplicate) {
      return false;
    }

    // Uploaded date range (doc.uploaded_at is ISO string)
    const from = filters.uploadedDateRange?.from ?? null;
    const to = filters.uploadedDateRange?.to ?? null;
    if (from !== null || to !== null) {
      const uploadedAt = doc.uploaded_at;
      if (!uploadedAt) return false;
      const docDate = uploadedAt.slice(0, 10); // YYYY-MM-DD
      if (from !== null && docDate < from) return false;
      if (to !== null && docDate > to) return false;
    }

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
