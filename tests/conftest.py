"""
Test configuration.

Ensures the project root (where domain.py, rules.py, etc. live)
is on sys.path so tests can import them as top-level modules.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
