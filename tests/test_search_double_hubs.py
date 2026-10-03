# Document:    Double Hub Extension Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from covering64.core import Universe, write_blocks

spec = importlib.util.spec_from_file_location(
    "search", Path(__file__).resolve().parents[1] / "scripts" / "search_double_hubs.py")
search = importlib.util.module_from_spec(spec)
spec.loader.exec_module(search)


def test_complete_nonanchor_extension_passes_both_checkers(tmp_path):
    universe = Universe.build(4, 2, 1)
    certificate = {"weights": [[2, 1, 1]], "lower_bound": [1, 1]}
    result = search.solve_extension(universe, [0], certificate, 2, 42, target=2)
    assert result["verification"]["valid"]
    assert result["complete_candidate_count"] == 1
    path = tmp_path / "control.txt"
    write_blocks(path, result["witness"])
    checker = Path(__file__).resolve().parents[1] / "scripts" / "check_cover.py"
    run = subprocess.run([sys.executable, str(checker), str(path), "--v", "4", "--k", "2",
                          "--t", "1", "--expected-blocks", "2"],
                         check=True, capture_output=True, text=True)
    assert json.loads(run.stdout)["valid"]


def test_lp_excludes_too_small_addition_budget():
    universe = Universe.build(4, 2, 1)
    certificate = {"weights": [[2, 1, 1]], "lower_bound": [1, 1]}
    result = search.solve_extension(universe, [0], certificate, 2, 42, target=1)
    assert result["status"] == "LP_CERTIFIED_INFEASIBLE"


def test_unclosed_link_and_duplicate_controls_are_rejected():
    universe = Universe.build(4, 2, 1)
    certificate = {"weights": [[2, 1, 1]], "lower_bound": [1, 1]}
    with pytest.raises(ValueError, match="close"):
        search.solve_extension(universe, [1], certificate, 2, 42, target=2)
    with pytest.raises(ValueError, match="duplicate"):
        search.solve_extension(universe, [0, 0], certificate, 2, 42, target=2)


def test_queue_recomputes_pools_for_larger_target():
    universe = Universe.build(5, 2, 1)
    cases = [{"retained_block_ids": [0], "identifier": "control", "first_class": "1",
              "certificate": {"weights": [[2, 1, 1]], "lower_bound": [1, 1]}}]
    assert search.build_pool_summary(universe, cases, [0], 1) == []
    small = search.build_pool_summary(universe, cases, [0], 2)
    larger = search.build_pool_summary(universe, cases, [0], 3)
    assert small[0]["pool_size"] == 2
    assert larger[0]["pool_size"] == larger[0]["complete_pool_size"] == 3


def test_low_bound_queue_uses_exact_bounds_and_all_classes():
    cases = [{"first_class": label} for label in ("1", "1", "4", "44", "47")]
    pools = [{"case": i, "bound": bound, "pool_size": 2, "complete_pool_size": 3}
             for i, bound in enumerate(([4, 3], [1, 1], [3, 2], [5, 3], [7, 4]))]
    queue = search.choose_queue(pools, cases, 5, 45, 1, True)
    assert [row["case"] for row in queue] == [1, 2, 3, 4]
    assert all(row["seconds"] == 45 for row in queue)
