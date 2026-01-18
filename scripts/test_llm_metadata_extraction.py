"""Test script to extract metadata using LLM (qwen3:4b) from PDF first pages.

This script tests LLM-based metadata extraction by sending first page text
to Ollama LLM and extracting structured metadata (title, authors, journal, year, DOI).
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, Optional

import pdfplumber
import requests

# Configuration - hardcoded for testing
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "qwen3:1.7b"  # Using qwen3:1.7b (smaller, requires less memory)


def extract_first_page_text(pdf_path: Path) -> dict:
    """
    Extract text from the first page of a PDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with extracted text
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) > 0:
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                if text:
                    return {
                        "filename": pdf_path.name,
                        "first_page_text": text.strip(),
                        "error": None,
                    }
                else:
                    return {
                        "filename": pdf_path.name,
                        "first_page_text": "",
                        "error": "No text extracted from first page",
                    }
            else:
                return {
                    "filename": pdf_path.name,
                    "first_page_text": "",
                    "error": "PDF has no pages",
                }
    except Exception as e:
        return {
            "filename": pdf_path.name,
            "first_page_text": "",
            "error": f"Error extracting text: {str(e)}",
        }


def extract_metadata_with_llm(text: str, max_length: int = 3000) -> Dict[str, Optional[str]]:
    """
    Extract metadata using LLM (Ollama qwen2.5:4b).
    
    Args:
        text: First page text from PDF
        max_length: Maximum characters to send to LLM
        
    Returns:
        Dictionary with extracted metadata (title, authors, journal, year, doi)
    """
    # Limit text length for LLM
    text_snippet = text[:max_length] if text else ""
    
    # Build structured extraction prompt - use Qwen chat format
    is_qwen = "qwen" in MODEL_NAME.lower()
    
    if is_qwen:
        # Qwen-specific chat template format
        prompt = f"""<|im_start|>system
You are a helpful AI assistant that extracts structured metadata from academic papers. Extract the following fields and return ONLY valid JSON (no markdown, no code blocks). Use null for missing fields.<|im_end|>
<|im_start|>user
Extract metadata from the following academic paper first page text:

{text_snippet}

Extract these fields:
- title: The paper title
- authors: Author names (comma-separated format, e.g., "Smith, J., Jones, B.")
- journal: Journal or publication name
- year: Publication year (4 digits as string, e.g., "2020")
- doi: DOI if present (format: 10.XXXX/XXXXX)

Return ONLY valid JSON with these exact keys. Example: {{"title": "Example Title", "authors": "Smith, J., Jones, B.", "journal": "Journal Name", "year": "2020", "doi": "10.1234/5678"}}<|im_end|>
<|im_start|>assistant
"""
    else:
        # Standard format for other models
        prompt = f"""Extract metadata from the following academic paper first page text.

Text:
{text_snippet}

Extract the following fields and return ONLY valid JSON (no markdown, no code blocks):
- title: The paper title
- authors: Author names (comma-separated format, e.g., "Smith, J., Jones, B.")
- journal: Journal or publication name
- year: Publication year (4 digits as string, e.g., "2020")
- doi: DOI if present (format: 10.XXXX/XXXXX)

Return ONLY valid JSON with these exact keys. Use null for missing fields.
Example: {{"title": "Example Title", "authors": "Smith, J., Jones, B.", "journal": "Journal Name", "year": "2020", "doi": "10.1234/5678"}}

JSON:"""
    
    try:
        # Call Ollama API
        generate_url = f"{OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "options": {
                "num_predict": 800,          # Max tokens to generate (was 500 → too short)
                "temperature": 0.7,          # Balanced creativity (0.5–0.8 is safe)
                "stop": ["<|im_end|>"],      # CRITICAL: stops at end of assistant turn
                "repeat_penalty": 1.0,       # No extra repetition penalty (Qwen handles well)
                "repeat_last_n": 64,         # Look back 64 tokens for repeats (default)
                "top_k": 40,                 # Consider top 40 tokens (standard)
                "top_p": 0.9,                # Nucleus sampling (good balance)
                "min_p": 0.05,               # Optional: ignore very low-prob tokens
                "num_ctx": 8192,             # Use full context window (if model supports it)
            },
            "stream": False,
        }
        
        response = requests.post(generate_url, json=payload, timeout=120)
        
        # Better error handling
        if response.status_code != 200:
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = error_data.get("error", response.text)
            except:
                error_detail = response.text[:500]
            
            return {
                "title": None,
                "authors": None,
                "journal": None,
                "year": None,
                "doi": None,
                "error": f"LLM API error (HTTP {response.status_code}): {error_detail}",
            }
        
        response.raise_for_status()
        result = response.json()
        llm_response = result.get("response", "").strip()
        thinking = result.get("thinking", "").strip()
        done_reason = result.get("done_reason", "")
        
        # Qwen models sometimes put output in thinking, check both
        # But we want the actual response, not thinking
        if not llm_response and done_reason == "length":
            # Model hit token limit - might need more tokens
            return {
                "title": None,
                "authors": None,
                "journal": None,
                "year": None,
                "doi": None,
                "error": f"LLM hit token limit (done_reason: {done_reason}). Response was empty, but thinking present: {thinking[:100] if thinking else 'N/A'}",
            }
        elif not llm_response:
            # Empty response but not due to length - might be stop token issue
            debug_info = f"done_reason: {done_reason}, thinking_length: {len(thinking)}"
            return {
                "title": None,
                "authors": None,
                "journal": None,
                "year": None,
                "doi": None,
                "error": f"LLM returned empty response. {debug_info}. Try increasing num_predict or checking stop tokens.",
            }
        
        # Try to extract JSON from response
        # LLM might return JSON wrapped in markdown or with extra text
        json_match = re.search(r'\{[^{}]*"title"[^{}]*\{[^{}]*\}', llm_response, re.DOTALL)
        if not json_match:
            # Try simpler pattern
            json_match = re.search(r'\{.*?\}', llm_response, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            try:
                metadata = json.loads(json_str)
                # Ensure all keys exist
                return {
                    "title": metadata.get("title"),
                    "authors": metadata.get("authors"),
                    "journal": metadata.get("journal"),
                    "year": metadata.get("year"),
                    "doi": metadata.get("doi"),
                    "error": None,
                }
            except json.JSONDecodeError as e:
                # Try to fix common JSON issues
                # Remove trailing commas
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                try:
                    metadata = json.loads(json_str)
                    return {
                        "title": metadata.get("title"),
                        "authors": metadata.get("authors"),
                        "journal": metadata.get("journal"),
                        "year": metadata.get("year"),
                        "doi": metadata.get("doi"),
                        "error": None,
                    }
                except json.JSONDecodeError:
                    pass
        
        # If JSON parsing failed, return with raw response for debugging
        return {
            "title": None,
            "authors": None,
            "journal": None,
            "year": None,
            "doi": None,
            "error": f"Could not parse JSON from LLM response. Response (first 300 chars): {llm_response[:300]}",
            "raw_response": llm_response[:500],  # Store first 500 chars for debugging
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "title": None,
            "authors": None,
            "journal": None,
            "year": None,
            "doi": None,
            "error": f"LLM request failed: {str(e)}",
        }
    except Exception as e:
        return {
            "title": None,
            "authors": None,
            "journal": None,
            "year": None,
            "doi": None,
            "error": f"LLM extraction error: {str(e)}",
        }


def test_llm_extraction(sample_data_dir: Path, limit: Optional[int] = None):
    """
    Test LLM-based metadata extraction on PDFs in sample_data directory.
    
    Args:
        sample_data_dir: Directory containing PDF files
        limit: Limit number of PDFs to test (None = all)
    """
    pdf_files = sorted(sample_data_dir.glob("*.pdf"))
    
    if limit:
        pdf_files = pdf_files[:limit]
    
    if not pdf_files:
        print(f"No PDF files found in {sample_data_dir}")
        return
    
    print(f"=" * 80)
    print(f"LLM METADATA EXTRACTION TEST")
    print(f"Model: {MODEL_NAME}")
    print(f"Ollama URL: {OLLAMA_BASE_URL}")
    print(f"Found {len(pdf_files)} PDF file(s)")
    print(f"=" * 80)
    print()
    
    # Test Ollama connection
    try:
        test_url = f"{OLLAMA_BASE_URL}/api/tags"
        response = requests.get(test_url, timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") if isinstance(m, dict) else str(m) for m in models]
            if MODEL_NAME not in model_names:
                print(f"[WARNING] Model {MODEL_NAME} not found in Ollama.")
                print(f"Available models: {', '.join(model_names)}")
                print(f"Will attempt to use {MODEL_NAME} anyway (Ollama may pull it).\n")
            else:
                print(f"[OK] Model {MODEL_NAME} found in Ollama.\n")
        else:
            print(f"[WARNING] Could not verify Ollama connection.\n")
    except Exception as e:
        print(f"[WARNING] Could not connect to Ollama: {str(e)}")
        print(f"Make sure Ollama is running at {OLLAMA_BASE_URL}\n")
    
    total_stats = {
        "title": 0,
        "authors": 0,
        "journal": 0,
        "year": 0,
        "doi": 0,
        "errors": 0,
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
            total_stats["errors"] += 1
            continue
        
        print(f"[OK] Text extracted ({len(result['first_page_text'])} chars)")
        
        # Extract metadata using LLM
        print(f"[INFO] Sending to LLM ({MODEL_NAME})...")
        metadata = extract_metadata_with_llm(result["first_page_text"])
        
        print(f"\nMETADATA EXTRACTION RESULTS:")
        print("-" * 80)
        
        if metadata.get("error"):
            print(f"[ERROR] {metadata['error']}")
            if "raw_response" in metadata:
                print(f"Raw LLM response (first 300 chars):")
                print(f"  {metadata['raw_response'][:300]}...")
            total_stats["errors"] += 1
        else:
            for field in ["title", "authors", "journal", "year", "doi"]:
                value = metadata.get(field)
                status = "[OK]" if value else "[MISSING]"
                
                if value:
                    # Truncate long values for display and handle Unicode
                    display_value = str(value)
                    if len(display_value) > 80:
                        display_value = display_value[:77] + "..."
                    # Encode to ASCII with errors='replace' to handle Unicode
                    try:
                        print(f"  {field.upper():10s} {status} {display_value}")
                    except UnicodeEncodeError:
                        # Fallback: replace problematic characters
                        safe_value = display_value.encode('ascii', 'replace').decode('ascii')
                        print(f"  {field.upper():10s} {status} {safe_value}")
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
    for field in ["title", "authors", "journal", "year", "doi"]:
        count = total_stats[field]
        percentage = (count / len(pdf_files)) * 100 if pdf_files else 0
        print(f"  {field.upper():10s} {count}/{len(pdf_files)} ({percentage:.1f}%)")
    
    if total_stats["errors"] > 0:
        print(f"\n[WARNING] {total_stats['errors']} PDF(s) had errors during extraction")
    
    print(f"{'=' * 80}")


def main():
    """Main entry point."""
    # Get script directory and project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Look for sample_data directory in project root
    sample_data_dir = project_root / "sample_data"
    
    if not sample_data_dir.exists():
        print(f"ERROR: sample_data directory not found.")
        print(f"Expected location: {sample_data_dir}")
        sys.exit(1)
    
    print(f"Scanning for PDFs in: {sample_data_dir}")
    print()
    
    # Test on all PDFs (use limit=2 for quick test)
    test_llm_extraction(sample_data_dir, limit=None)


if __name__ == "__main__":
    main()
