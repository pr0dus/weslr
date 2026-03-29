#!/usr/bin/env python3
"""
Read any document file (txt, docx, pdf) with automatic format detection.
Usage: read_any_file.py <file> [--limit N] [--encoding auto]
"""

import sys
import os
import subprocess

def read_any_file(filepath, max_lines=None, encoding='auto'):
    """Read file based on extension"""
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return None
    
    ext = os.path.splitext(filepath)[1].lower()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if ext == '.txt':
        cmd = ['python3', f'{script_dir}/read_text.py', filepath]
        if max_lines:
            cmd.append(f'--limit {max_lines}')
        if encoding != 'auto':
            cmd.append(f'--encoding {encoding}')
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout + result.stderr
    
    elif ext == '.docx':
        cmd = ['python3', f'{script_dir}/read_docx.py', filepath]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout + result.stderr
    
    elif ext == '.pdf':
        cmd = ['python3', f'{script_dir}/read_pdf.py', filepath]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout + result.stderr
    
    else:
        return f"Error: Unsupported file type: {ext}\nSupported: .txt, .docx, .pdf"

def main():
    filepath = None
    max_lines = None
    encoding = 'auto'
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--limit' and i + 1 < len(sys.argv):
            max_lines = int(sys.argv[i + 1])
            i += 2
        elif arg == '--encoding' and i + 1 < len(sys.argv):
            encoding = sys.argv[i + 1]
            i += 2
        elif not arg.startswith('-'):
            filepath = arg
            i += 1
        else:
            i += 1
    
    if not filepath:
        print("Usage: python read_any_file.py <file> [--limit N] [--encoding auto]")
        sys.exit(1)
    
    output = read_any_file(filepath, max_lines, encoding)
    print(output)

if __name__ == '__main__':
    main()
