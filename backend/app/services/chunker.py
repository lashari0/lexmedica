"""Document chunking service for splitting text into semantic chunks."""

import logging
import re
from typing import List, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


class Chunker:
    """Service for splitting documents into semantic chunks."""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        """
        Initialize chunker with configuration.

        Args:
            chunk_size: Maximum chunk size in characters (defaults to settings)
            chunk_overlap: Overlap between chunks in characters (defaults to settings)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def chunk_text(
        self,
        text: str,
        document_id: str,
        filename: str,
    ) -> List[Dict[str, Any]]:
        """
        Split text into semantic chunks with metadata.

        Strategy:
        1. Split by paragraphs (double newline)
        2. For large paragraphs, split by sentences
        3. Apply overlap between chunks
        4. Preserve metadata for each chunk

        Args:
            text: Text content to chunk
            document_id: Document identifier
            filename: Original filename

        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text or not text.strip():
            return []

        chunks = []
        paragraphs = self._split_into_paragraphs(text)

        current_chunk = ""
        current_start = 0
        chunk_index = 0

        for para_idx, paragraph in enumerate(paragraphs):
            # If paragraph fits in current chunk, add it
            if len(current_chunk) + len(paragraph) + 1 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Save current chunk if it exists
                if current_chunk:
                    chunk_data = self._create_chunk_metadata(
                        current_chunk,
                        document_id,
                        filename,
                        chunk_index,
                        current_start,
                        current_start + len(current_chunk),
                    )
                    chunks.append(chunk_data)
                    chunk_index += 1

                    # Apply overlap: start next chunk with overlap from previous
                    overlap_text = self._get_overlap_text(
                        current_chunk, self.chunk_overlap
                    )
                    # Calculate new start position: end of previous chunk minus overlap
                    previous_end = current_start + len(current_chunk)
                    current_start = previous_end - len(overlap_text)
                    current_chunk = overlap_text + "\n\n" + paragraph
                else:
                    # Paragraph is too large, split by sentences
                    if len(paragraph) > self.chunk_size:
                        sentence_chunks = self._split_large_paragraph(
                            paragraph, document_id, filename, chunk_index, current_start
                        )
                        chunks.extend(sentence_chunks)
                        chunk_index += len(sentence_chunks)
                        if sentence_chunks:
                            # Set start for next chunk with overlap
                            last_chunk = sentence_chunks[-1]
                            overlap_text = self._get_overlap_text(
                                last_chunk["text"], self.chunk_overlap
                            )
                            current_chunk = overlap_text
                            current_start = last_chunk["end_char"]
                        else:
                            current_chunk = ""
                            current_start += len(paragraph)
                    else:
                        # Small paragraph that doesn't fit in current chunk
                        # Start position should be calculated from previous chunk end
                        if chunks:
                            last_chunk = chunks[-1]
                            current_start = last_chunk["end_char"]
                        current_chunk = paragraph

        # Add final chunk
        if current_chunk:
            chunk_data = self._create_chunk_metadata(
                current_chunk,
                document_id,
                filename,
                chunk_index,
                current_start,
                current_start + len(current_chunk),
            )
            chunks.append(chunk_data)

        return chunks

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs (double newline separator)."""
        # Split by double newline, but preserve single newlines within paragraphs
        paragraphs = re.split(r"\n\s*\n", text)
        # Clean up and filter empty paragraphs
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_large_paragraph(
        self,
        paragraph: str,
        document_id: str,
        filename: str,
        start_chunk_index: int,
        start_char: int,
    ) -> List[Dict[str, Any]]:
        """
        Split a large paragraph into sentence-based chunks.

        Args:
            paragraph: Paragraph text to split
            document_id: Document identifier
            filename: Original filename
            start_chunk_index: Starting chunk index
            start_char: Starting character position

        Returns:
            List of chunk dictionaries
        """
        # Split by sentences (period, exclamation, question mark followed by space)
        sentences = re.split(r"([.!?]\s+)", paragraph)
        # Recombine sentences with their punctuation
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                combined_sentences.append(sentences[i] + sentences[i + 1])
            else:
                combined_sentences.append(sentences[i])
        if len(sentences) % 2 == 1:
            combined_sentences.append(sentences[-1])

        chunks = []
        current_chunk = ""
        current_start = start_char
        chunk_index = start_chunk_index

        for sentence in combined_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                # Save current chunk
                if current_chunk:
                    chunk_data = self._create_chunk_metadata(
                        current_chunk,
                        document_id,
                        filename,
                        chunk_index,
                        current_start,
                        current_start + len(current_chunk),
                    )
                    chunks.append(chunk_data)
                    chunk_index += 1

                    # Apply overlap
                    overlap_text = self._get_overlap_text(
                        current_chunk, self.chunk_overlap
                    )
                    # Calculate new start position: end of previous chunk minus overlap
                    previous_end = current_start + len(current_chunk)
                    current_start = previous_end - len(overlap_text)
                    current_chunk = overlap_text + " " + sentence
                else:
                    # Sentence itself is too large, split it by words
                    if len(sentence) > self.chunk_size:
                        word_chunks = self._split_by_words(
                            sentence, document_id, filename, chunk_index, current_start
                        )
                        chunks.extend(word_chunks)
                        chunk_index += len(word_chunks)
                        if word_chunks:
                            last_chunk = word_chunks[-1]
                            overlap_text = self._get_overlap_text(
                                last_chunk["text"], self.chunk_overlap
                            )
                            current_chunk = overlap_text
                            current_start = last_chunk["end_char"]
                        else:
                            current_chunk = ""
                            current_start += len(sentence)
                    else:
                        # Small sentence that doesn't fit in current chunk
                        # Start position should be calculated from previous chunk end
                        if chunks:
                            last_chunk = chunks[-1]
                            current_start = last_chunk["end_char"]
                        else:
                            current_start = start_char
                        current_chunk = sentence
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        # Add final chunk
        if current_chunk:
            chunk_data = self._create_chunk_metadata(
                current_chunk,
                document_id,
                filename,
                chunk_index,
                current_start,
                current_start + len(current_chunk),
            )
            chunks.append(chunk_data)

        return chunks

    def _split_by_words(
        self,
        text: str,
        document_id: str,
        filename: str,
        start_chunk_index: int,
        start_char: int,
    ) -> List[Dict[str, Any]]:
        """
        Split text by words as last resort for very long sentences.

        Args:
            text: Text to split
            document_id: Document identifier
            filename: Original filename
            start_chunk_index: Starting chunk index
            start_char: Starting character position

        Returns:
            List of chunk dictionaries
        """
        words = text.split()
        chunks = []
        current_chunk = ""
        current_start = start_char
        chunk_index = start_chunk_index

        for word in words:
            if len(current_chunk) + len(word) + 1 > self.chunk_size:
                if current_chunk:
                    chunk_data = self._create_chunk_metadata(
                        current_chunk,
                        document_id,
                        filename,
                        chunk_index,
                        current_start,
                        current_start + len(current_chunk),
                    )
                    chunks.append(chunk_data)
                    chunk_index += 1

                    # Apply overlap
                    overlap_text = self._get_overlap_text(
                        current_chunk, self.chunk_overlap
                    )
                    # Calculate new start position: end of previous chunk minus overlap
                    previous_end = current_start + len(current_chunk)
                    current_start = previous_end - len(overlap_text)
                    current_chunk = overlap_text + " " + word
                else:
                    # Single word is too large, truncate it
                    current_chunk = word[: self.chunk_size]
                    current_start = start_char
            else:
                if current_chunk:
                    current_chunk += " " + word
                else:
                    current_chunk = word

        # Add final chunk
        if current_chunk:
            chunk_data = self._create_chunk_metadata(
                current_chunk,
                document_id,
                filename,
                chunk_index,
                current_start,
                current_start + len(current_chunk),
            )
            chunks.append(chunk_data)

        return chunks

    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """
        Get overlap text from the end of a chunk.

        Args:
            text: Chunk text
            overlap_size: Number of characters to overlap

        Returns:
            Overlap text (last N characters)
        """
        if not text or overlap_size <= 0:
            return ""
        # Try to get overlap at word boundary
        if len(text) <= overlap_size:
            return text
        overlap = text[-overlap_size:]
        # Try to start at word boundary
        first_space = overlap.find(" ")
        if first_space > 0 and first_space < overlap_size // 2:
            overlap = overlap[first_space + 1 :]
        return overlap

    def _create_chunk_metadata(
        self,
        text: str,
        document_id: str,
        filename: str,
        chunk_index: int,
        start_char: int,
        end_char: int,
    ) -> Dict[str, Any]:
        """
        Create chunk dictionary with text and metadata.

        Args:
            text: Chunk text content
            document_id: Document identifier
            filename: Original filename
            chunk_index: Chunk index (0-based)
            start_char: Starting character position in original text
            end_char: Ending character position in original text

        Returns:
            Chunk dictionary with text and metadata
        """
        return {
            "text": text,
            "document_id": document_id,
            "filename": filename,
            "chunk_index": chunk_index,
            "start_char": start_char,
            "end_char": end_char,
        }
