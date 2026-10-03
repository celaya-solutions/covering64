# Document:    Core Escape LNS Tests
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import importlib.util
from pathlib import Path

import pytest

from covering64.core import Universe, write_blocks

spec = importlib.util.spec_from_file_location(
    "escape", Path(__file__).resolve().parents[1] / "scripts" / "core_escape_lns.py")
escape = importlib.util.module_from_spec(spec)
spec.loader.exec_module(escape)


def test_escape_can_leave_a_core_without_losing_coverage(tmp_path):
    universe = Universe.build(4, 2, 1)
    # The starting matching {12,34} is a cover. The alternate matching
    # {13,24} proves that core overlap zero is feasible.
    result = escape.solve_step(universe, [0, 5], [0, 5], [0, 5], 2, 12,
                               max_missing=0, core_cap=0)
    assert result["uncovered"] == 0
    assert result["core_overlap"] == 0
    assert len(result["selected_ids"]) == 2
    path = tmp_path / "cover.txt"
    write_blocks(path, [universe.blocks[i] for i in result["selected_ids"]])
    assert escape.check_state(path, universe, 2)["standalone"]["valid"]


def test_partial_candidate_verifiers_agree(tmp_path):
    universe = Universe.build(4, 2, 1)
    result = escape.solve_step(universe, [0], [0], [], 2, 14, max_missing=2)
    assert result["uncovered"] == 2
    path = tmp_path / "partial.txt"
    write_blocks(path, [universe.blocks[i] for i in result["selected_ids"]])
    checks = escape.check_state(path, universe, 1)
    assert checks["standalone"]["uncovered_count"] == 2
    assert not checks["standalone"]["valid"]


def test_damaged_control_is_rejected():
    universe = Universe.build(4, 2, 1)
    with pytest.raises(ValueError, match="duplicate"):
        escape.solve_step(universe, [0, 0], [0], [], 2, 14)
    with pytest.raises(ValueError, match="invalid"):
        escape.solve_step(universe, [0], [1], [], 2, 14)


def test_full_link_bounds_reject_some_partial_covers_but_accept_full_control():
    universe = Universe.build(4, 3, 2)
    partial = escape.solve_step(universe, [0, 1], [0, 1], [], 2, 22,
                                max_missing=2)
    assert partial["uncovered"] == 1
    restricted = escape.solve_step(universe, [0, 1], [0, 1], [], 2, 22,
                                   max_missing=2, full_link_bounds=True)
    assert restricted["status"] == "INFEASIBLE"
    full = escape.solve_step(universe, [0, 1, 2], [0, 1, 2], [], 2, 22,
                             max_missing=2, full_link_bounds=True)
    assert full["uncovered"] == 0
