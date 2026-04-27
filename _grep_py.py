import os, sys

def grep_py(pattern, root, exclude_dirs):
    results = []
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(dirpath, f)
                try:
                    lines = open(path, errors='ignore').readlines()
                    for i, line in enumerate(lines, 1):
                        if pattern in line:
                            rel = path.replace(root + '/', '')
                            results.append(f"{rel}:{i}: {line.rstrip()}")
                except:
                    pass
    return results

root = "/data/data/com.termux/files/home/.openclaw/workspace"
pattern = sys.argv[1]
exclude = {"__pycache__", ".git", "node_modules", "weslr-tia-openness-bridge", "weslr-ui", "dist", "_out_of_scope"}

results = grep_py(pattern, root, exclude)
for r in results:
    print(r)