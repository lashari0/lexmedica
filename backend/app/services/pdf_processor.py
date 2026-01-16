"""PDF text extraction service."""

import logging
from pathlib import Path
from typing import Dict, Any, Tuple

import pdfplumber
import PyPDF2

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Service for extracting text from PDF files."""

    # Minimum text length to consider PDF as text-based (not scanned)
    MIN_TEXT_LENGTH = 100

    def extract_text(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract text from PDF file.

        Tries pdfplumber first (better extraction), falls back to PyPDF2 if needed.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary with:
                - text: Extracted text content
                - needs_ocr: Boolean indicating if PDF appears to be scanned
                - method: Extraction method used ("pdfplumber" or "pypdf2")
                - error: Error message if extraction failed (optional)

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a valid PDF
        """
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        # Try pdfplumber first (better text extraction)
        try:
            text, method = self._extract_with_pdfplumber(file_path)
            if text:
                needs_ocr = self._detect_ocr_needed(text)
                return {
                    "text": text,
                    "needs_ocr": needs_ocr,
                    "method": method,
                }
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}, trying PyPDF2")

        # Fallback to PyPDF2
        try:
            text, method = self._extract_with_pypdf2(file_path)
            if text:
                needs_ocr = self._detect_ocr_needed(text)
                return {
                    "text": text,
                    "needs_ocr": needs_ocr,
                    "method": method,
                }
        except Exception as e:
            logger.error(f"PyPDF2 extraction also failed: {e}")
            return {
                "text": "",
                "needs_ocr": True,
                "method": "none",
                "error": f"Failed to extract text: {str(e)}",
            }

        # If we get here, both methods failed
        return {
            "text": "",
            "needs_ocr": True,
            "method": "none",
            "error": "Both pdfplumber and PyPDF2 failed to extract text",
        }

    def _extract_with_pdfplumber(self, file_path: Path) -> Tuple[str, str]:
        """
        Extract text using pdfplumber.

        Returns:
            Tuple of (extracted_text, method_name)
        """
        text_parts = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:
            raise Exception(f"pdfplumber error: {str(e)}")

        text = "\n\n".join(text_parts)
        return text.strip(), "pdfplumber"

    def _extract_with_pypdf2(self, file_path: Path) -> Tuple[str, str]:
        """
        Extract text using PyPDF2.

        Returns:
            Tuple of (extracted_text, method_name)
        """
        text_parts = []
        try:
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    raise Exception("PDF is encrypted and cannot be read")

                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:
            raise Exception(f"PyPDF2 error: {str(e)}")

        text = "\n\n".join(text_parts)
        return text.strip(), "pypdf2"

    def _detect_ocr_needed(self, text: str) -> bool:
        """
        Detect if PDF likely needs OCR (scanned image PDF).

        Heuristic: If extracted text is very short or mostly whitespace,
        the PDF is likely a scanned image.

        Args:
            text: Extracted text content

        Returns:
            True if OCR is likely needed, False otherwise
        """
        if not text:
            return True

        # Remove whitespace and check length
        text_without_whitespace = "".join(text.split())
        if len(text_without_whitespace) < self.MIN_TEXT_LENGTH:
            return True

        # Check if text is mostly whitespace
        if len(text_without_whitespace) / len(text) < 0.3:
            return True

        return False
