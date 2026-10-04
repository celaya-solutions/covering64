# Document:    Additional Radius Four Runner Fake Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e03f4431b21801adcb020392f9cf1eb265a517c896e09622f6f221777950f14d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Exercise the reviewed fake-process harness with extra terminal cases; no solve."""

import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
PRODUCER = HERE.with_name("radius-four-feasibility-repair-v2")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = PRODUCER / "runner_controls.py"
    spec = importlib.util.spec_from_file_location("reviewed_fake_harness", target)
    controls = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(controls)
    partial, cover = controls.synthetic_record(), controls.synthetic_record(True)
    cases = [
        (
            "infeasible-is-status-only",
            json.dumps({"status": "INFEASIBLE", "saved_states": []}),
            {},
            0,
            0,
            "INFEASIBLE",
        ),
        (
            "model-invalid-is-status-only",
            json.dumps({"status": "MODEL_INVALID", "saved_states": []}),
            {},
            0,
            0,
            "MODEL_INVALID",
        ),
        (
            "feasible-partial",
            json.dumps({"status": "FEASIBLE", "saved_states": [partial]}),
            {},
            0,
            0,
            "FEASIBLE",
        ),
        (
            "nonzero-child-exit-overrides-status",
            json.dumps({"status": "OPTIMAL", "saved_states": [partial]}),
            {},
            0,
            1,
            "ERROR",
        ),
        (
            "recover-mixed-complete-receipts",
            '{"unfinished":',
            {
                "callback-0001-receipt.json": json.dumps(partial),
                "callback-0002-receipt.json": json.dumps(cover),
                "callback-0003-receipt.json": '{"unfinished":',
            },
            2,
            -9,
            "WATCHDOG_TIMEOUT",
        ),
        (
            "missing-child-recovers-partial",
            None,
            {"callback-0001-receipt.json": json.dumps(partial)},
            0,
            1,
            "ERROR",
        ),
    ]
    with patch.object(
        cp_model.CpSolver, "solve", side_effect=AssertionError("native solve forbidden")
    ) as guard:
        rows = [controls.run_case(*case) for case in cases]
        readonly = controls.check_readonly_vector_validation()
        assert guard.call_count == 0
    assert rows[2]["synthetic_partial_flag"] and not rows[2]["synthetic_cover_flag"]
    assert rows[4]["recovered_records"] == 2
    assert rows[4]["synthetic_partial_flag"] and rows[4]["synthetic_cover_flag"]
    assert rows[5]["recovered_records"] == 1
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "native_solve_guard_calls": 0,
        "real_process_launches": 0,
        "runner_sha256": sha(PRODUCER / "execute.py"),
        "producer_controls_source_sha256": sha(target),
        "review_checker_sha256": sha(Path(__file__)),
        "cases": rows,
        "readonly_validation": readonly,
        "scope": "Additional cases use the source-reviewed producer fake-process harness. "
        "They exercise reporting only and do not construct actual candidate families or covers.",
    }
    output = HERE / "fake-controls-review.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "optimizer_calls": 0, "review_sha256": sha(output)}))


if __name__ == "__main__":
    main()
