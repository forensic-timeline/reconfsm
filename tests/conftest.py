"""
conftest.py — shared pytest fixtures for the reconfsm test suite.
"""

from pathlib import Path
import pytest


from reconfsm.fsm.fsm import load_machine_from_json


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
EXAMPLE_JSON = EXAMPLES_DIR / "web_activity_20250605_182216.json"


@pytest.fixture
def dummy_json_path():
    """Absolute path to the bundled web_activity example JSON."""
    if not EXAMPLE_JSON.exists():
        pytest.fail(f"Example JSON not found: {EXAMPLE_JSON}")
    return str(EXAMPLE_JSON)


@pytest.fixture
def dummy_machine(dummy_json_path):
    """Pre-loaded FSMachine from the example web_activity JSON."""
    return load_machine_from_json(dummy_json_path)