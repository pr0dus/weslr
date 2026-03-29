#!/usr/bin/env python3
"""
Extract text from DOCX files.
Dependencies: python-docx
Usage: python read_docx.py <file.docx>
"""

import sys
import os

def extract_docx(filepath):
    """Extract text from Word document"""
    try:
        import docx
        doc = docx.Document(filepath)
        text = []
        for para in doc.paragraphs:
            text.append(para.text)
        return '\n'.join(text)
    except ImportError:
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python read_docx.py <file.docx>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    text = extract_docx(filepath)
    
    if text:
        print(text)
    else:
        print("Error: python-docx library not installed.")
        print("Install: pip install python-docx")
        sys.exit(1)

if __name__ == '__main__':
    main()
