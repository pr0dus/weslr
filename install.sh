#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

python3 --version

echo "CircleForge is ready."
echo
if command -v ollama >/dev/null 2>&1; then
  echo "Ollama detected: $(ollama --version 2>/dev/null | head -1 || echo yes)"
else
  echo "Ollama not detected (optional). CircleForge can still run with fallback behavior."
fi

echo
echo "Quick start:"
echo "  python3 main.py setup"
echo
echo "Guided setup will ask for:"
echo "  - agent count"
echo "  - tick count (0 = infinite)"
echo "  - tick interval seconds"
echo "  - dashboard auto-refresh seconds"
echo
echo "After setup, CircleForge prints the exact dashboard path and file:// URL to open in your browser."
