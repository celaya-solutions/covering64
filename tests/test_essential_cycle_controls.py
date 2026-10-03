# Document:    Degree-Preserving Long-Cycle Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      232eea97f5f1b4e1d22861c841abdc5a1907889c31fa317f6acd25628ac5e0e0
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cycle_candidate_checker", ROOT / "scripts/verify_essential_heuristic.py")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)
SEED = ROOT / "experiments/2026-10-03/essential-regular-heuristic/pilot-2026100317-h8-u0-p0.txt"


@pytest.fixture(scope="module")
def cycle_run(tmp_path_factory):
    compiler = shutil.which("clang++")
    if compiler is None:
        pytest.skip("C++ compiler is not available")
    directory = tmp_path_factory.mktemp("cycle-controls")
    binary = directory / "search"
    subprocess.run([compiler, "-std=c++17", "-O2", "-o", str(binary),
                    str(ROOT / "scripts/essential_regular_heuristic.cpp")], check=True)
    prefix = directory / "control"
    result = subprocess.run([str(binary), str(SEED), "2026100341", "0.2", str(prefix)],
                            check=True, capture_output=True, text=True)
    return directory, [json.loads(line) for line in result.stdout.splitlines()]


def test_long_cycles_have_independently_validated_controls(cycle_run):
    _, events = cycle_run
    controls = [event for event in events if event["event"] == "move_control"]
    assert {event["changed"] for event in controls} == {4, 5, 6, 7, 8}
    for event in controls:
        after = CHECKER.analyze(Path(event["path"]).read_text())
        assert after["holes"] == event["holes"]
        assert after["unsupported_count"] == event["unsupported"]
        assert after["pair_deficit"] == event["pair_deficit"]
        before_blocks = set(Path(event["before_path"]).read_text().splitlines())
        after_blocks = set(Path(event["path"]).read_text().splitlines())
        assert len(after_blocks - before_blocks) == event["changed"]
        assert len(before_blocks - after_blocks) == event["changed"]


def test_long_cycle_rejections_restore_recounted_state(cycle_run):
    _, events = cycle_run
    finish = events[-1]
    assert finish["event"] == "finish"
    assert finish.get("long_cycle_rollback_audits", 0) >= 5
    assert sum(finish["applied_by_size"][4:]) >= 5
    final = CHECKER.analyze(Path(finish["final_path"]).read_text())
    assert final["holes"] <= 10
    assert finish["reservoir_size"] >= 1
