"""Test package; enables `python3 -m unittest` from the repository root."""

from __future__ import annotations

import unittest
from pathlib import Path


def load_tests(
    loader: unittest.TestLoader,
    standard_tests: unittest.TestSuite,
    pattern: str,
) -> unittest.TestSuite:
    start = Path(__file__).resolve().parent
    return loader.discover(start_dir=str(start), pattern="test*.py", top_level_dir=str(start.parent))