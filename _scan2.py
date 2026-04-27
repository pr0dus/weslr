import sys
f = "/data/data/com.termux/files/home/.openclaw/workspace/dialogue.py"
content = open(f).read()
for i, line in enumerate(content.splitlines(), 1):
    ll = line.lower()
    if "boundary_hints" in ll or "reply_shape" in ll:
        print(f"{i}: {line}")