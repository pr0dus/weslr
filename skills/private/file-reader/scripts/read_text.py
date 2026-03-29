#!/usr/bin/env python3
"""
Read text files with encoding detection and line limits.
Usage: python read_text.py <file.txt> [--limit N] [--encoding auto]
"""

import sys
import os
import chardet

def detect_encoding(filepath):
    """Detect file encoding"""
    with open(filepath, 'rb') as f:
        raw = f.read(10000)
    result = chardet.detect(raw)
    return result.get('encoding', 'utf-8')

def read_text_file(filepath, max_lines=None, encoding='auto'):
    """Read text file with optional line limit"""
    if encoding == 'auto':
        encoding = detect_encoding(filepath)
    
    try:
        with open(filepath, 'r', encoding=encoding, errors='replace') as f:
            lines = []
            for i, line in enumerate(f):
                if max_lines and i >= max_lines:
                    lines.append(f"\n[... {i - max_lines + 1} more lines omitted ...]")
                    break
                lines.append(line.rstrip('\n'))
            return '\n'.join(lines)
    except Exception as e:
        return f"Error reading file: {e}"

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
        print("Usage: python read_text.py <file.txt> [--limit N] [--encoding auto]")
        sys.exit(1)
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    text = read_text_file(filepath, max_lines, encoding)
    print(text)

if __name__ == '__main__':
    main()
