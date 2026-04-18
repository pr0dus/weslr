"""Weslr PDF Text Extraction (v1)

Safe, text-only PDF extraction for Weslr.
Expects and returns only text - no execution, no binary extraction.

Architecture:
  - extract_text_from_pdf_bytes() - Core extraction from bytes
  - extract_text_from_pdf_path() - Convenience wrapper for file paths
  - Safe extraction only - no code execution, no image extraction

Safety Boundaries:
  - Text-only output (no images, no binary data)
  - No code execution from PDF content
  - No file paths outside workspace allowed
  - No subprocess or import execution from PDF
"""

from __future__ import annotations

import io
import os
import re
from pathlib import Path
from typing import Union

# Priority: pdfplumber (preferred) -> PyPDF2 (fallback)
# Both are pure Python, no native dependencies
pdfplumber = None
pypdf = None

try:
    import pdfplumber
    pdfplumber = pdfplumber
except ImportError:
    pass  # pdfplumber is optional

try:
    import PyPDF2
    pypdf = PyPDF2
except ImportError:
    pypdf = None  # PyPDF2 is optional


__all__ = [
    "extract_text_from_pdf_bytes",
    "extract_text_from_pdf_path",
    "PDFTextExtractionError",
]


class PDFTextExtractionError(Exception):
    """Raised when PDF text extraction fails."""
    pass


def _is_safe_path(filepath: str, workspace_dir: str) -> bool:
    """Check if filepath is within workspace directory.
    
    Prevents path traversal attacks by ensuring
    all paths are within the workspace directory.
    
    Args:
        filepath: The path to check
        workspace_dir: The workspace directory (safe root)
        
    Returns:
        True if path is safe, False otherwise
    """
    try:
        workspace = Path(workspace_dir).resolve()
        path = Path(filepath).resolve()
        # Check if path is within workspace
        return str(path).startswith(str(workspace) + os.sep) or path == workspace
    except Exception:
        return False


def extract_text_from_pdf_bytes(
    pdf_bytes: bytes,
    max_pages: int | None = None,
    max_chars: int | None = 100000,
) -> str:
    """Extract text from PDF bytes safely.
    
    This is the core safe extraction function. It:
    - Uses pdfplumber (preferred) or PyPDF2 (fallback)
    - Only extracts text content
    - No code execution, no image extraction
    - Respects page and character limits
    
    Args:
        pdf_bytes: PDF file content as bytes
        max_pages: Maximum pages to extract (None = no limit)
        max_chars: Maximum characters to return (default: 100000)
        
    Returns:
        Extracted text as string
        
    Raises:
        PDFTextExtractionError: If extraction fails
    """
    if not pdfplumber and not pypdf:
        raise PDFTextExtractionError(
            "No PDF backend installed. Install with: pip install pdfplumber or pip install PyPDF2"
        )
    
    if not isinstance(pdf_bytes, bytes):
        raise PDFTextExtractionError("pdf_bytes must be bytes type")
    
    if len(pdf_bytes) == 0:
        return ""
    
    # Safety check: limit PDF size
    MAX_PDF_SIZE = 10 * 1024 * 1024  # 10MB max
    if len(pdf_bytes) > MAX_PDF_SIZE:
        raise PDFTextExtractionError(f"PDF too large: {len(pdf_bytes)} bytes (max {MAX_PDF_SIZE})")
    
    # Try pdfplumber first (preferred)
    if pdfplumber:
        return _extract_with_pdfplumber(pdf_bytes, max_pages, max_chars)
    
    # Fallback to PyPDF2
    if pypdf:
        return _extract_with_pypdf(pdf_bytes, max_pages, max_chars)
    
    raise PDFTextExtractionError("No PDF backend available")


def _extract_with_pdfplumber(
    pdf_bytes: bytes,
    max_pages: int | None,
    max_chars: int | None,
) -> str:
    """Extract text from PDF using pdfplumber."""
    text_parts = []
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        pages_to_process = pdf.pages
        if max_pages is not None:
            pages_to_process = pdf.pages[:max_pages]
        
        for page in pages_to_process:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    
    text = "\n\n".join(text_parts)
    
    if max_chars and len(text) > max_chars:
        text = text[:max_chars] + "\n... [truncated]"
    
    return text


def _extract_with_pypdf(
    pdf_bytes: bytes,
    max_pages: int | None,
    max_chars: int | None,
) -> str:
    """Extract text from PDF using PyPDF2."""
    reader = None
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        
        text_parts = []
        pages = reader.pages
        
        if max_pages is not None:
            pages = pages[:max_pages]
        
        for page in pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        text = "\n\n".join(text_parts)
        
        if max_chars and len(text) > max_chars:
            text = text[:max_chars] + "\n... [truncated]"
        
        return text
    finally:
        if reader:
            try:
                reader.close()
            except Exception:
                pass


def extract_text_from_pdf_path(
    filepath: str,
    workspace_dir: str | None = None,
    max_pages: int | None = None,
    max_chars: int | None = 100000,
) -> str:
    """Extract text from PDF file path safely.
    
    This is a convenience wrapper that:
    - Validates the path is within workspace
    - Calls extract_text_from_pdf_bytes() internally
    - Returns only text content
    
    Args:
        filepath: Path to PDF file (must be within workspace)
        workspace_dir: Workspace directory (default: current directory)
        max_pages: Maximum pages to extract (None = no limit)
        max_chars: Maximum characters to return (default: 100000)
        
    Returns:
        Extracted text as string
        
    Raises:
        PDFTextExtractionError: If path is unsafe or extraction fails
    """
    workspace = workspace_dir or str(Path(__file__).resolve().parent.parent)
    
    # Safety: validate path is within workspace
    if not _is_safe_path(filepath, workspace):
        raise PDFTextExtractionError(
            f"Path traversal attempt: {filepath} is outside workspace {workspace}"
        )
    
    if not os.path.exists(filepath):
        raise PDFTextExtractionError(f"PDF file not found: {filepath}")
    
    # Read file as bytes
    try:
        with open(filepath, "rb") as f:
            pdf_bytes = f.read()
    except Exception as e:
        raise PDFTextExtractionError(f"Failed to read PDF file: {e}") from e
    
    # Delegate to safe bytes extraction
    return extract_text_from_pdf_bytes(
        pdf_bytes,
        max_pages=max_pages,
        max_chars=max_chars,
    )


def sanitize_extracted_text(text: str) -> str:
    """Sanitize extracted text for safe processing.
    
    This ensures text is clean and safe for:
    - LLM processing
    - Storage in JSON
    - Display in UI
    
    Args:
        text: Extracted text
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Remove null bytes and control characters
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    
    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    
    return text


def estimate_pages_from_bytes(pdf_bytes: bytes) -> int:
    """Estimate number of pages from PDF bytes.
    
    Used for safety limits before full parsing.
    
    Args:
        pdf_bytes: PDF file content
        
    Returns:
        Estimated page count
    """
    if not isinstance(pdf_bytes, bytes):
        return 0
    
    # PDFs are typically 10-100 KB per page
    # This is a rough estimate for safety limits
    if len(pdf_bytes) == 0:
        return 0
    
    avg_bytes_per_page = 25000  # 25 KB average
    return max(1, len(pdf_bytes) // avg_bytes_per_page)
