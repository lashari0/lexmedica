"""Chunk validation rules and validation service."""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ChunkValidator:
    """Service for validating document chunks according to rules."""

    def __init__(
        self,
        min_length: int = 10,
        max_length: int = 10000,
        require_text: bool = True,
    ):
        """
        Initialize chunk validator.

        Args:
            min_length: Minimum chunk length in characters
            max_length: Maximum chunk length in characters
            require_text: Whether to require non-empty text
        """
        self.min_length = min_length
        self.max_length = max_length
        self.require_text = require_text

    def validate_chunk(self, chunk: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate a single chunk.

        Args:
            chunk: Chunk dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if "text" not in chunk:
            return False, "Chunk missing 'text' field"
        
        text = chunk.get("text", "")
        
        # Check text requirement
        if self.require_text and (not text or not text.strip()):
            return False, "Chunk text is empty"
        
        # Check length constraints
        text_length = len(text)
        if text_length < self.min_length:
            return False, f"Chunk too short: {text_length} < {self.min_length} characters"
        
        if text_length > self.max_length:
            return False, f"Chunk too long: {text_length} > {self.max_length} characters"
        
        # Check required metadata fields
        if "document_id" not in chunk:
            return False, "Chunk missing 'document_id' field"
        
        if "chunk_index" not in chunk:
            return False, "Chunk missing 'chunk_index' field"
        
        return True, None

    def validate_chunks(self, chunks: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[str]]:
        """
        Validate a list of chunks.

        Args:
            chunks: List of chunk dictionaries to validate

        Returns:
            Tuple of (valid_chunks, error_messages)
        """
        valid_chunks = []
        errors = []
        
        for i, chunk in enumerate(chunks):
            is_valid, error = self.validate_chunk(chunk)
            if is_valid:
                valid_chunks.append(chunk)
            else:
                chunk_id = chunk.get("document_id", "unknown")
                chunk_idx = chunk.get("chunk_index", i)
                error_msg = f"Chunk {chunk_id}_chunk_{chunk_idx}: {error}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        if errors:
            logger.warning(f"Validation found {len(errors)} invalid chunks out of {len(chunks)}")
        
        return valid_chunks, errors

    def filter_valid_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out invalid chunks, keeping only valid ones.

        Args:
            chunks: List of chunk dictionaries to filter

        Returns:
            List of valid chunks
        """
        valid_chunks, _ = self.validate_chunks(chunks)
        return valid_chunks
