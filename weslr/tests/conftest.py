"""
conftest.py — pytest configuration for weslr tests.
Sets up the import path so individual test modules can import weslr.* modules
without requiring the full tests/__init__.py package import chain.
"""
import sys
from pathlib import Path

# Ensure the repo root is on sys.path so `import weslr` resolves.
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))