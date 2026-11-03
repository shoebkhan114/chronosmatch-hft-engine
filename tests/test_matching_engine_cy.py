"""Run the existing matching-engine tests against the Cython engine.

Skipped automatically when the extension is not built
(python setup.py build_ext --inplace).
"""
import importlib

import pytest

cy = pytest.importorskip("src.matching_engine_cy")
base = importlib.import_module("tests.test_matching_engine")

# Point the original tests at the Cython engine.
base.MatchingEngine = cy.MatchingEngine

for _name in dir(base):
    if _name.startswith("test_"):
        globals()[_name] = getattr(base, _name)
