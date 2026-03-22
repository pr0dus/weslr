#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "setup" ]]; then
  shift
  python3 main.py setup "$@"
  exit 0
fi

if [[ "${1:-}" == "serve" ]]; then
  shift
  python3 main.py serve "$@"
  exit 0
fi

python3 main.py run --ticks 0 --interval 60 "$@"
