"""Evidence assembler for grouping and organizing retrieved evidence."""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class EvidenceAssembler:
    """Service for grouping and organizing retrieved evidence by section and logical flow."""

    def assemble_evidence(
        self,
        results: List[Dict[str, Any]],
        group_by_document: bool = True,
        group_by_section: bool = False,
        sort_by_score: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Assemble and organize evidence from search results.

        Args:
            results: List of search result dictionaries
            group_by_document: Whether to group results by document
            group_by_section: Whether to group results by section (requires section metadata)
            sort_by_score: Whether to sort by similarity score

        Returns:
            Organized list of evidence chunks
        """
        if not results:
            return []
        
        # Sort by score if requested
        if sort_by_score:
            results = sorted(
                results,
                key=lambda x: x.get("score", 0.0),
                reverse=True,
            )
        
        # Group by document if requested
        if group_by_document:
            grouped = self._group_by_document(results)
            logger.debug(f"Grouped {len(results)} results into {len(grouped)} documents")
            return grouped
        
        # Group by section if requested
        if group_by_section:
            grouped = self._group_by_section(results)
            logger.debug(f"Grouped {len(results)} results into {len(grouped)} sections")
            return grouped
        
        return results

    def _group_by_document(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group results by document ID.

        Args:
            results: List of search results

        Returns:
            List of grouped results
        """
        document_groups: Dict[str, List[Dict[str, Any]]] = {}
        
        for result in results:
            metadata = result.get("metadata", {})
            doc_id = metadata.get("document_id", "unknown")
            
            if doc_id not in document_groups:
                document_groups[doc_id] = []
            
            document_groups[doc_id].append(result)
        
        # Flatten back to list, maintaining document grouping order
        grouped_results = []
        for doc_id, doc_results in document_groups.items():
            grouped_results.extend(doc_results)
        
        return grouped_results

    def _group_by_section(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group results by section (if section metadata is available).

        Args:
            results: List of search results

        Returns:
            List of grouped results by section
        """
        section_groups: Dict[str, List[Dict[str, Any]]] = {}
        
        for result in results:
            metadata = result.get("metadata", {})
            section = metadata.get("section", "unknown")
            
            if section not in section_groups:
                section_groups[section] = []
            
            section_groups[section].append(result)
        
        # Flatten back to list, maintaining section grouping order
        grouped_results = []
        for section, section_results in section_groups.items():
            grouped_results.extend(section_results)
        
        return grouped_results

    def create_evidence_summary(
        self,
        results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Create a summary of evidence from search results.

        Args:
            results: List of search results

        Returns:
            Dictionary with evidence summary statistics
        """
        if not results:
            return {
                "total_chunks": 0,
                "unique_documents": 0,
                "average_score": 0.0,
                "score_range": (0.0, 0.0),
            }
        
        unique_docs = set()
        scores = []
        
        for result in results:
            metadata = result.get("metadata", {})
            doc_id = metadata.get("document_id")
            if doc_id:
                unique_docs.add(doc_id)
            
            score = result.get("score", 0.0)
            scores.append(score)
        
        return {
            "total_chunks": len(results),
            "unique_documents": len(unique_docs),
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "score_range": (min(scores), max(scores)) if scores else (0.0, 0.0),
        }
