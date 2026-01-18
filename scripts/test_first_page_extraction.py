"""Test script to extract and analyze metadata from PDF first pages.

This script extracts the first page text from all PDFs in the sample_data directory
and tests metadata extraction (title, authors, journal, year, DOI) to validate
patterns for Step 9 implementation.
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add backend directory to path to import app modules if needed
script_dir = Path(__file__).parent
project_root = script_dir.parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

import pdfplumber


def extract_first_page_text(pdf_path: Path) -> dict:
    """
    Extract text from the first page of a PDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with extracted text and metadata
    """
    result = {
        "filename": pdf_path.name,
        "first_page_text": "",
        "num_lines": 0,
        "text_length": 0,
        "method": None,
        "error": None,
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) > 0:
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                if text:
                    result["first_page_text"] = text.strip()
                    result["num_lines"] = len(text.strip().split("\n"))
                    result["text_length"] = len(text)
                    result["method"] = "pdfplumber"
                else:
                    result["error"] = "No text extracted from first page"
            else:
                result["error"] = "PDF has no pages"
    except Exception as e:
        result["error"] = f"Error extracting text: {str(e)}"
        result["method"] = "pdfplumber (failed)"
    
    return result


def extract_title(text_lines: List[str], text_start: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Extract title from document text.
    
    Returns:
        Tuple of (title, line_number) or (None, None) if not found
    """
    if not text_lines:
        return None, None
    
    # Check first 10 lines for potential title
    for line_idx, line in enumerate(text_lines[:10], 1):
        line = line.strip()
        # Skip very short or very long lines
        if len(line) < 10 or len(line) > 200:
            continue
        
        # Skip lines that look like metadata
        metadata_keywords = [
            "abstract", "keywords", "doi:", "http", "www", "email",
            "author", "affiliation", "university", "department",
            "corresponding", "received", "accepted", "published",
            "journal", "volume", "issue", "pages", "contents",
        ]
        if any(keyword in line.lower() for keyword in metadata_keywords):
            continue
        
        # Check if line starts with capital and has reasonable length
        if line and line[0].isupper():
            # Additional validation: title shouldn't be all caps
            if not line.isupper() and not line.replace(" ", "").isdigit():
                return line, line_idx
    
    # Fallback: longest meaningful line in first 5 lines
    candidates = [(line.strip(), idx) for idx, line in enumerate(text_lines[:5], 1) 
                  if 15 <= len(line.strip()) <= 200]
    if candidates:
        # Prefer lines that start with capital letter
        capitalized = [(line, idx) for line, idx in candidates if line and line[0].isupper()]
        if capitalized:
            return max(capitalized, key=lambda x: len(x[0]))
        return max(candidates, key=lambda x: len(x[0]))
    
    return None, None


def extract_authors(text_lines: List[str], text_start: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Extract author names from document text.
    
    Returns:
        Tuple of (authors_string, line_number) or (None, None) if not found
    """
    if not text_lines:
        return None, None
    
    # Patterns for author lines
    author_patterns = [
        # Last, First Initial. Middle Initial. format
        r"([A-Z][a-z]+(?:\s*,\s*[A-Z]\.?\s*[A-Z]?\.?)*(?:\s+and\s+[A-Z][a-z]+(?:\s*,\s*[A-Z]\.?\s*[A-Z]?\.?)*)*)",
        # First Last and First Last format
        r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+and\s+[A-Z][a-z]+\s+[A-Z][a-z]+)*)",
    ]
    
    # Check lines 2-15 for authors (usually after title)
    for line_idx, line in enumerate(text_lines[1:15], 2):
        line = line.strip()
        # Skip very long lines (likely not authors)
        if len(line) > 300:
            continue
        
        # Skip lines with metadata keywords
        skip_keywords = ["abstract", "keywords", "doi:", "journal", "volume", "pages", "introduction"]
        if any(keyword in line.lower() for keyword in skip_keywords):
            continue
        
        # Try to match author patterns
        for pattern in author_patterns:
            match = re.search(pattern, line)
            if match:
                authors = match.group(1).strip()
                # Validate: should contain at least one name-like pattern
                if len(authors) >= 5 and len(authors.split()) >= 2:
                    # Remove common suffixes
                    if not any(suffix in authors.lower() for suffix in ["department", "university", "institute"]):
                        return authors, line_idx
    
    return None, None


def extract_journal(text: str, text_lines: List[str]) -> Tuple[Optional[str], Optional[int]]:
    """
    Extract journal name from document text.
    
    Returns:
        Tuple of (journal_name, line_number) or (None, None) if not found
    """
    # Look for journal patterns
    journal_patterns = [
        r"Journal\s+of\s+([A-Z][a-zA-Z\s]+)",
        r"([A-Z][a-zA-Z\s]+Journal)",
        r"([A-Z][a-zA-Z\s]+Review)",
    ]
    
    for line_idx, line in enumerate(text_lines[:20], 1):
        line = line.strip()
        if "journal" in line.lower():
            # Try to extract journal name
            for pattern in journal_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    journal = match.group(1).strip()
                    if 3 <= len(journal) <= 100:
                        return journal, line_idx
    
    # Also check for full journal names in text
    full_text_lower = text.lower()
    journal_markers = ["journal of", "journal:", "published in"]
    for marker in journal_markers:
        if marker in full_text_lower:
            idx = full_text_lower.find(marker)
            # Extract surrounding text
            snippet = text[max(0, idx-50):min(len(text), idx+150)]
            for pattern in journal_patterns:
                match = re.search(pattern, snippet, re.IGNORECASE)
                if match:
                    journal = match.group(1).strip()
                    if 3 <= len(journal) <= 100:
                        return journal, None
    
    return None, None


def extract_year(text: str, text_lines: List[str]) -> Tuple[Optional[str], Optional[int]]:
    """
    Extract publication year from document text.
    
    Returns:
        Tuple of (year_string, line_number) or (None, None) if not found
    """
    # Look for 4-digit years (1990-2025 range for realistic publication years)
    year_pattern = r"\b(19[9]\d|20[0-2]\d)\b"
    
    for line_idx, line in enumerate(text_lines[:20], 1):
        matches = re.findall(year_pattern, line)
        if matches:
            # Take the most recent year found
            year = max(matches)
            return year, line_idx
    
    # Also search in full text if not found in first lines
    matches = re.findall(year_pattern, text[:2000])  # Search first 2000 chars
    if matches:
        year = max(matches)
        return year, None
    
    return None, None


def extract_doi(text: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Extract DOI from document text.
    
    Returns:
        Tuple of (doi_string, line_number) or (None, None) if not found
    """
    # DOI pattern: 10.XXXX/XXXXX
    doi_pattern = r"10\.\d{4,9}/[\S]+"
    
    lines = text.split("\n")
    for line_idx, line in enumerate(lines, 1):
        match = re.search(doi_pattern, line)
        if match:
            doi = match.group(0).strip()
            # Clean up trailing punctuation
            doi = doi.rstrip(".,;:)")
            return doi, line_idx
    
    # Also check if DOI appears as "doi:" prefix
    doi_label_pattern = r"doi[:\s]+(10\.\d{4,9}/[\S]+)"
    match = re.search(doi_label_pattern, text, re.IGNORECASE)
    if match:
        doi = match.group(1).strip().rstrip(".,;:)")
        return doi, None
    
    return None, None


def test_metadata_extraction(text: str, text_lines: List[str]) -> Dict[str, Dict]:
    """
    Test metadata extraction on given text.
    
    Returns:
        Dictionary with extraction results for each metadata field
    """
    results = {}
    
    # Extract title
    title, title_line = extract_title(text_lines, text)
    results["title"] = {
        "value": title,
        "line": title_line,
        "success": title is not None,
    }
    
    # Extract authors
    authors, authors_line = extract_authors(text_lines, text)
    results["authors"] = {
        "value": authors,
        "line": authors_line,
        "success": authors is not None,
    }
    
    # Extract journal
    journal, journal_line = extract_journal(text, text_lines)
    results["journal"] = {
        "value": journal,
        "line": journal_line,
        "success": journal is not None,
    }
    
    # Extract year
    year, year_line = extract_year(text, text_lines)
    results["year"] = {
        "value": year,
        "line": year_line,
        "success": year is not None,
    }
    
    # Extract DOI
    doi, doi_line = extract_doi(text)
    results["doi"] = {
        "value": doi,
        "line": doi_line,
        "success": doi is not None,
    }
    
    return results


def analyze_metadata_extraction(sample_data_dir: Path, show_text: bool = False, max_lines: int = 20):
    """
    Extract and test metadata from first page of all PDFs in sample_data directory.
    
    Args:
        sample_data_dir: Directory containing PDF files
        show_text: Whether to display extracted text
        max_lines: Maximum number of text lines to display if show_text is True
    """
    pdf_files = sorted(sample_data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {sample_data_dir}")
        return
    
    print(f"=" * 80)
    print(f"METADATA EXTRACTION TEST")
    print(f"Found {len(pdf_files)} PDF file(s)")
    print(f"=" * 80)
    print()
    
    total_stats = {
        "title": 0,
        "authors": 0,
        "journal": 0,
        "year": 0,
        "doi": 0,
    }
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"{'=' * 80}")
        print(f"PDF {i}/{len(pdf_files)}: {pdf_file.name}")
        print(f"{'=' * 80}")
        
        # Extract first page text
        result = extract_first_page_text(pdf_file)
        
        if result["error"]:
            print(f"[ERROR] {result['error']}")
            print()
            continue
        
        print(f"[SUCCESS] Text extracted ({result['text_length']} chars, {result['num_lines']} lines)")
        
        if show_text:
            print(f"\nFirst {max_lines} lines:")
            print("-" * 80)
            lines = result["first_page_text"].split("\n")
            for line_num, line in enumerate(lines[:max_lines], 1):
                if len(line) > 150:
                    line = line[:147] + "..."
                print(f"{line_num:3d} | {line}")
            if len(lines) > max_lines:
                print(f"     ... ({len(lines) - max_lines} more lines)")
            print("-" * 80)
        
        # Test metadata extraction
        text_lines = result["first_page_text"].split("\n")
        metadata_results = test_metadata_extraction(result["first_page_text"], text_lines)
        
        print(f"\nMETADATA EXTRACTION RESULTS:")
        print("-" * 80)
        
        for field, data in metadata_results.items():
            status = "[OK]" if data["success"] else "[MISSING]"
            line_info = f" (line {data['line']})" if data["line"] else ""
            
            if data["success"]:
                # Truncate long values for display
                value = data["value"]
                if len(value) > 80:
                    value = value[:77] + "..."
                print(f"  {field.upper():10s} {status} {value}{line_info}")
                total_stats[field] += 1
            else:
                print(f"  {field.upper():10s} {status} Not found")
        
        print()
    
    # Summary statistics
    print(f"{'=' * 80}")
    print(f"EXTRACTION SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total PDFs processed: {len(pdf_files)}")
    print(f"\nSuccess rates:")
    for field, count in total_stats.items():
        percentage = (count / len(pdf_files)) * 100 if pdf_files else 0
        print(f"  {field.upper():10s} {count}/{len(pdf_files)} ({percentage:.1f}%)")
    print(f"{'=' * 80}")


def main():
    """Main entry point."""
    # Get script directory and project root
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent.absolute()
    
    # Look for sample_data directory in project root
    sample_data_dir = project_root / "sample_data"
    
    if not sample_data_dir.exists():
        print(f"ERROR: sample_data directory not found.")
        print(f"Expected location: {sample_data_dir}")
        print(f"Script directory: {script_dir}")
        print(f"Project root: {project_root}")
        sys.exit(1)
    
    print(f"Scanning for PDFs in: {sample_data_dir}")
    print()
    
    # Run metadata extraction test (set show_text=True to see extracted text)
    analyze_metadata_extraction(sample_data_dir, show_text=False)


if __name__ == "__main__":
    main()
