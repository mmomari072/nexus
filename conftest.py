"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

# Add repository root to Python path
root = Path(__file__).parent
sys.path.insert(0, str(root))
