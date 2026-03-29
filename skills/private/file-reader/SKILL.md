---
name: file-reader
description: Read text, DOCX, and PDF files. Use when needing to extract and summarize content from documents (.txt, .docx, .pdf files) for research, analysis, or reference. Supports line-limited reading for large files and automatic encoding detection for text files.
---

# File Reader Skill

This skill provides tools for reading and extracting content from common document formats.

## Available Scripts

### `read_text.py`
- Reads plain text files with encoding detection
- Supports `--limit N` to read first N lines
- Usage: `python read_text.py <file.txt> [--limit N]`

### `read_docx.py`
- Extracts text from Word documents (.docx)
- Dependencies: `python-docx`
- Usage: `python read_docx.py <file.docx>`

### `read_pdf.py`
- Extracts text from PDFs
- Tries multiple libraries: pdfplumber, PyPDF2, pdfminer.six
- Usage: `python read_pdf.py <file.pdf> [--extractor extractor_name]`

## When to Use This Skill

Use this skill when:

1. **User asks to read a document** - "Read this PDF", "Show me the text from this file"
2. **Research or analysis** - Need to extract content from documents for context
3. **Large file handling** - Use `--limit` to avoid token overflow
4. **Unknown encoding** - Text reader auto-detects encoding

## Workflow

1. Identify the file type and location
2. Use appropriate script based on extension
3. Apply `--limit` for large files (>10k lines)
4. Summarize or extract key information as needed

## Dependencies

Install if missing:

```bash
pip install python-docx pdfplumber pypdf2 pdfminer.six chardet
```
