#!/usr/bin/env python3
import sys, re

path = '/data/data/com.termux/files/home/.openclaw/workspace/interpretation.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = '''    if isinstance(cooc_data, dict):
        cooc_list = cooc_data.get("pairs", cooc_data.get("cooccurrences", []))
    elif isinstance(cooc_data, list):
        cooc_list = cooc_data
    else:
        cooc_list = []'''

new = '''    if isinstance(cooc_data, dict):
        cooc_list = cooc_data.get("pairs", {})
        if isinstance(cooc_list, dict):
            cooc_list = [
                {"pair": key, "entities": key.split("|"), **value}
                for key, value in cooc_list.items()
                if isinstance(value, dict)
            ]
        elif not isinstance(cooc_list, list):
            cooc_list = []
    elif isinstance(cooc_data, list):
        cooc_list = cooc_data
    else:
        cooc_list = []'''

if old not in content:
    print("PATTERN NOT FOUND")
    sys.exit(1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content.replace(old, new, 1))

print("PATCHED OK")
