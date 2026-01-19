"""Document metadata service for attaching metadata to chunks."""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class MetadataService:
    """Service for attaching and managing document metadata."""

    def attach_metadata(
        self,
        chunks: list[Dict[str, Any]],
        document_id: str,
        filename: str,
        file_path: Optional[Path] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> list[Dict[str, Any]]:
        """
        Attach metadata to document chunks.

        Args:
            chunks: List of chunk dictionaries
            document_id: Document identifier
            filename: Original filename
            file_path: Optional path to the source file
            additional_metadata: Optional additional metadata to attach

        Returns:
            List of chunks with metadata attached
        """
        metadata = {
            "document_id": document_id,
            "filename": filename,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        
        # Add file metadata if available
        if file_path and file_path.exists():
            file_stat = file_path.stat()
            metadata.update({
                "file_size": file_stat.st_size,
                "file_modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            })
        
        # Add additional metadata
        if additional_metadata:
            metadata.update(additional_metadata)
        
        # Attach metadata to each chunk
        for chunk in chunks:
            chunk["metadata"] = metadata.copy()
            # Also add metadata fields directly to chunk for compatibility
            chunk.update(metadata)
        
        logger.debug(f"Attached metadata to {len(chunks)} chunks for document {document_id}")
        return chunks

    def extract_document_metadata(
        self,
        file_path: Path,
        document_id: str,
        filename: str,
    ) -> Dict[str, Any]:
        """
        Extract metadata from a document file.

        Args:
            file_path: Path to the document file
            document_id: Document identifier
            filename: Original filename

        Returns:
            Dictionary of metadata
        """
        metadata = {
            "document_id": document_id,
            "filename": filename,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        
        if file_path.exists():
            file_stat = file_path.stat()
            metadata.update({
                "file_size": file_stat.st_size,
                "file_modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                "file_extension": file_path.suffix.lower(),
            })
        
        return metadata
