"""Run the frozen speed vocabulary and overlap vectors as offline smoke tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from test_benchmark_speed_contract import ContractTests  # noqa: F401,E402


if __name__ == '__main__':
    import unittest
    unittest.main()
