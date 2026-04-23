#!/usr/bin/env python3
"""Verify chat_ui.py JS syntax and contamination display logic."""
import sys

with open('chat_ui.py') as f:
    html = f.read()

start = html.find('<script>')
end = html.find('</script>', start)
js = html[start+8:end]

open_braces = js.count('{')
close_braces = js.count('}')
open_parens = js.count('(')
close_parens = js.count(')')

print(f'JS braces: {open_braces} open, {close_braces} close, diff={open_braces-close_braces}')
print(f'JS parens: {open_parens} open, {close_parens} close, diff={open_parens-close_parens}')
print(f'high risk advisory: {"contamination-advisory.high" in js}')
print(f'medium risk advisory: {"contamination-advisory.medium" in js}')
print(f'source_signals: {"source_signals" in js}')
print(f'refreshState contamination: {"_contamination_metadata" in html}')
print(f'sendMessage contamination: {"data._contamination_metadata" in html}')
print('VERIFICATION COMPLETE')