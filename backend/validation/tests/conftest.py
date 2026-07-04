import copy
import json
import sys
from pathlib import Path

import pytest

# Make `import validation` work when pytest runs from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def golden() -> dict:
    """A fully valid Bupa outpatient consultation invoice."""
    return copy.deepcopy(json.loads((FIXTURES / "golden_valid.json").read_text()))
