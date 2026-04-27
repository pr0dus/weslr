import os, re, sys

workspace = "/data/data/com.termux/files/home/.openclaw/workspace"
syms = sys.argv[1:]
exclude = {"__pycache__", ".git", "node_modules", "weslr-tia-openness-bridge", "weslr-ui", "dist", "_out_of_scope", "_staging"}

for sym in syms:
    print(f"=== {sym} ===")
    found = False
    for root, dirs, files in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in exclude]
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                try:
                    content = open(path, "r", errors="ignore").read()
                    for m in re.finditer(re.escape(sym), content):
                        line_no = content[:m.start()].count("\n") + 1
                        rel = path.replace(workspace + "/", "")
                        print(f"  {rel}:{line_no}")
                        found = True
                except:
                    pass
    if not found:
        print("  NOT FOUND")