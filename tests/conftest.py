"""
conftest.py — shared pytest fixtures for the reconfsm test suite.

IMPORTANT – fsm.py import bootstrap
------------------------------------
reconfsm/fsm/fsm.py uses bare-name imports designed to be run from inside its
own directory:

    from pathfinding import pathfinding_simulation
    from graph import graph_simulation
"""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock
import pytest


# ---------------------------------------------------------------------------
# Bootstrap: stub out the bare 'pathfinding' and 'graph' imports in fsm.py
#
# fsm.py does:  from pathfinding import pathfinding_simulation
#               from graph import graph_simulation
#
# These are bare-name imports that only work when run from the fsm/ directory.
# When imported as a package, Python finds the installed PyPI 'pathfinding'
# package instead, which doesn't expose pathfinding_simulation → ImportError.
#
# Fix: inject lightweight stubs into sys.modules BEFORE reconfsm.fsm.fsm is
# imported for the first time. All subsequent imports hit the cache.
# ---------------------------------------------------------------------------

def _make_stub(module_name, **attrs):
    mod = types.ModuleType(module_name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


if "reconfsm.fsm.fsm" not in sys.modules:
    sys.modules.setdefault(
        "pathfinding",
        _make_stub("pathfinding", pathfinding_simulation=MagicMock()),
    )
    sys.modules.setdefault(
        "graph",
        _make_stub("graph", graph_simulation=MagicMock()),
    )

from reconfsm.fsm.fsm import load_machine_from_json  # noqa: E402


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