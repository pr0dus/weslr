#!/usr/bin/env bash
set -euo pipefail
python3 main.py run --ticks 0 --interval 60 "$@"
