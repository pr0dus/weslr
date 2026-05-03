#!/usr/bin/env python3
import re

text = 'efficiency 150 percent'
print(f"text: {text!r}")
print(f"len: {len(text)}")

# Test the regex
for p in [r'efficiencies?', r'efficiency', r'[a-z]+']:
    m = re.search(p, text)
    print(f"pattern {p!r}: {m}")
    if m:
        print(f"  matched: {m.group()!r} at {m.span()}")

# Step by step
print()
m = re.search(r'efficiencies?', text)
print(f"efficiencies? match: {m}")
if m:
    print(f"  group: {m.group()!r}")
else:
    # Try findall
    fa = re.findall(r'efficiencies?', text)
    print(f"findall: {fa}")
    # Try split
    parts = re.split(r'efficiencies?', text)
    print(f"split: {parts}")
    # What's happening - match 'efficiency' char by char
    # efficient = e f f i c i e n t
    # efficienc  = e f f i c i e n c
    # Wait no: efficiency = efficient + y
    # efficient = e f f i c i e n t
    # efficiency = e f f i c i e n c y
    # So efficients? = efficient + (optional 'y' + 's')
    # efficient ends with 't', not 'c'
    # efficiency has 'cy' at end
    # So 'efficiencies?' would match 'efficien' + 'c' + (optional 'y' + 's')
    # No wait. Let me parse 'efficiencies?' as a regex:
    # efficient = e f f i c i e n t
    # [ies]? = optionally match i, e, or s
    # Wait: ()? is optional group. (ies)? means optionally match the sequence i, e, s
    # So the pattern matches: efficient followed by optionally (i, then e, then s)
    # 'efficiency' doesn't end with 'ies', so no match
    print()
    print("'efficiency' ends with 'y', not 'ies', so efficiencies? won't match it")
    print("The pattern efficients? means 'efficient' + optionally 'ies'")
    print("'efficiency' is 'efficient' + 'y', so it doesn't match")