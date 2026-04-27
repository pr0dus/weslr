import sys
path = "/data/data/com.termux/files/home/.openclaw/workspace/dialogue.py"
content = open(path).read()
for line_no, line in enumerate(content.splitlines(), 1):
    if "_resolve_active_artifact" in line or "_resolve_user_id" in line:
        print(f"{line_no}: {line}")