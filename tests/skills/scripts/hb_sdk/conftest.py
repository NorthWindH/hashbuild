import sys
from pathlib import Path

# Make helpers.py importable without package config changes
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from helpers import init, task_create


@pytest.fixture()
def task1(tmp_path: Path) -> Path:
    """Initialized repo with one task ready for steps."""
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    return tmp_path
