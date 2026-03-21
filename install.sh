#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

python3 --version

echo "CircleForge v0.0.52 is ready."
echo
if command -v ollama >/dev/null 2>&1; then
  echo "Ollama detected: $(ollama --version 2>/dev/null | head -1 || echo yes)"
else
  echo "Ollama not detected (optional). CircleForge can still run with fallback behavior."
fi

echo
echo "Quick start:"
echo "  python3 main.py init --reset --agents 4"
echo "  python3 main.py tick"
echo "  python3 main.py show-world"
echo "  python3 main.py dashboard"
echo
echo "Open dashboard/index.html after rendering the dashboard."
