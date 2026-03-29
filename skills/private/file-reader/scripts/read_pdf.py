#!/usr/bin/env python3
"""
Extract text from PDF files.
Dependencies: PyPDF2, pdfplumber, or pdfminer.six (install one)
Usage: python read_pdf.py <file.pdf> [--extractor extractor_name]
"""

import sys
import os

def extract_with_pypdf2(filepath):
    """Extract text using PyPDF2"""
    try:
        import PyPDF2
        text = []
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text() or '')
        return '\n'.join(text)
    except ImportError:
        return None

def extract_with_pdfplumber(filepath):
    """Extract text using pdfplumber (better for complex layouts)"""
    try:
        import pdfplumber
        text = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text.append(page.extract_text() or '')
        return '\n'.join(text)
    except ImportError:
        return None

def extract_with_pdfminer(filepath):
    """Extract text using pdfminer.six"""
    try:
        from pdfminer.high_level import extract_text
        return extract_text(filepath)
    except ImportError:
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python read_pdf.py <file.pdf> [--extractor extractor_name]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    extractor = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    # Try specified extractor or all available
    extractors = []
    if extractor:
        extractors.append(extractor)
    else:
        extractors = ['pdfplumber', 'pypdf2', 'pdfminer']
    
    text = None
    used_extractor = None
    
    for ext in extractors:
        if ext == 'pdfplumber':
            text = extract_with_pdfplumber(filepath)
            used_extractor = 'pdfplumber'
        elif ext == 'pypdf2':
            text = extract_with_pypdf2(filepath)
            used_extractor = 'pypdf2'
        elif ext == 'pdfminer':
            text = extract_with_pdfminer(filepath)
            used_extractor = 'pdfminer'
        
        if text:
            break
    
    if text:
        print(f"[Extracted with {used_extractor}]")
        print(text)
    else:
        print("Error: No PDF extraction library available.")
        print("Install one: pip install pdfplumber pypdf2 pdfminer.six")
        sys.exit(1)

if __name__ == '__main__':
    main()
