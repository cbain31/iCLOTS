"""Reproduce SCI-002 directly from the unchanged legacy normalization loop."""

import ast
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.unit


def test_legacy_normalization_modifies_only_row_three():
    path = Path(__file__).parents[2] / "videoedit" / "normalize_folderapp.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    loop = next(node for node in ast.walk(tree) if isinstance(node, ast.For)
                and isinstance(node.target, ast.Name) and node.target.id == "i")
    original = np.arange(6 * 4 * 3, dtype=np.uint8).reshape(6, 4, 3)
    actual = original.copy()
    module = ast.Module(body=[loop], type_ignores=[])
    exec(compile(module, str(path), "exec"), {"np": np, "img": actual, "l": 3})
    assert np.array_equal(actual[[0, 1, 2, 4, 5]], original[[0, 1, 2, 4, 5]])
    assert not np.array_equal(actual[3], original[3])
