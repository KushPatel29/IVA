import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.warehouse import build_warehouse  # noqa: E402


@pytest.fixture(scope="session")
def con():
    return build_warehouse()
