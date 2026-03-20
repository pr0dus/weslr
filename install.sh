#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

python3 --version

echo "CircleForge v0.0.2 is ready."
echo
echo "Quick start:"
echo "  python3 main.py init --reset --agents 4"
echo "  python3 main.py tick"
echo "  python3 main.py run --ticks 10 --interval 60"
