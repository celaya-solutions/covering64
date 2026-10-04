# Document:    Radius-Four Feasibility Runner Fake-Process Controls
# Version:     v2.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      cec59a2db8e0d1684e3dad5945e0199170160abbd3022adf5f6598e81f956ce4
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Exercise runner recording with synthetic processes; never invoke a solver."""

import contextlib
import importlib.util
import io
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from google.protobuf import text_format
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(
        f"radius_four_controls_{name}", HERE / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_record(cover=False):
    return {
        "label": "synthetic-control-only",
        "actual_metrics": {"holes": 0 if cover else 11},
        "cover_found": cover,
        "feasible_partial": not cover,
        "feasibility_target_met": True,
    }


def run_case(name, child, receipts, timeouts, returncode, expected_status):
    runner, prep = load("execute"), load("prepare")
    calls = {"launch": 0, "wait": 0, "terminate": 0, "kill": 0}
    with tempfile.TemporaryDirectory(prefix="radius-four-fake-") as directory:
        root = Path(directory)
        destination = root / "public"
        destination.mkdir()
        run = root / "run"
        gate = root / "synthetic-gate.json"
        gate.write_text("{}\n")
        args = SimpleNamespace(gate=gate, gate_sha256=prep.sha(gate))
        expected = {
            "manifest_sha256": "synthetic-manifest",
            "model_sha256": "synthetic-model",
            "parameters_sha256": "synthetic-parameters",
            "runner_sha256": prep.sha(HERE / "execute.py"),
        }

        class FakeProcess:
            def __init__(self, command, **kwargs):
                calls["launch"] += 1
                assert command[-1] == "--inner"
                assert kwargs["cwd"] == root
                self.returncode = None
                if child is not None:
                    (run / "child-result.json").write_text(child)
                for filename, contents in receipts.items():
                    (run / filename).write_text(contents)

            def wait(self, timeout=None):
                calls["wait"] += 1
                if calls["wait"] <= timeouts:
                    raise runner.subprocess.TimeoutExpired("synthetic", timeout)
                self.returncode = returncode
                return returncode

            def terminate(self):
                calls["terminate"] += 1

            def kill(self):
                calls["kill"] += 1

        with (
            patch.object(runner, "ROOT", root),
            patch.object(runner, "HERE", destination),
            patch.object(runner, "RUN", run),
            patch.object(runner.subprocess, "Popen", FakeProcess),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            runner.outer(args, prep, {"scope": "synthetic control only"}, expected)
        result = json.loads((destination / "result.json").read_text())
        assert result["status"] == expected_status
        assert calls["launch"] == result["single_child_launches"] == 1
        assert not result["relaunch"] and not result["budget_transfer"]
        assert result["optimizer_call_upper_bound"] == 1
        assert result["watchdog"]["fired"] is (timeouts > 0)
        assert calls["terminate"] == int(timeouts > 0)
        assert calls["kill"] == int(timeouts > 1)
        assert result["watchdog"]["terminate_sent"] is (timeouts > 0)
        assert result["watchdog"]["kill_sent"] is (timeouts > 1)
        assert result["watchdog"]["deadline_seconds"] == 330
        assert result["watchdog"]["grace_seconds"] == 5
        malformed = child is not None and child.startswith('{"unfinished')
        assert (result["child_terminal_error"] is not None) is malformed
        if malformed:
            assert result["child_result"] is None
            assert result["optimizer_calls"] is None
            assert result["child_terminal_error"].startswith("JSONDecodeError:")
        assert result["cover_found"] is any(row["cover_found"] for row in result["saved_states"])
        assert result["feasible_partial_found"] is any(
            row["feasible_partial"] for row in result["saved_states"]
        )
        assert result["feasibility_target_met"] is bool(result["saved_states"])
        assert all(prep.sha(root / path) == digest for path, digest in result["raw_files"].items())
        return {
            "name": name,
            "passed": True,
            "status": result["status"],
            "calls": calls,
            "recovered_records": len(result["saved_states"]),
            "synthetic_cover_flag": result["cover_found"],
            "synthetic_partial_flag": result["feasible_partial_found"],
            "child_terminal_error_recorded": malformed,
        }


def check_readonly_vector_validation():
    prep = load("prepare")
    prior, _ = prep.bound_inputs()
    model_path = ROOT / prior["model_path"]
    proto = cp_model_pb2.CpModelProto()
    text_format.Parse(model_path.read_text(), proto)
    proto.ClearField("objective")
    proto.ClearField("solution_hint")
    blocks = prep.helper_module().parse(prep.BASE.read_text())
    rank = {block: index for index, block in enumerate(prep.prior_module().SETS[5])}
    ids = sorted(rank[block] for block in blocks)
    actual = prep.recount(ids, prior["core_rows"], ids)
    native = cp_model.CpModel()
    assert native.proto.parse_text_format(text_format.MessageToString(proto))
    before = str(native.proto)
    assert not native.proto.has_solution_hint()
    assert not native.has_objective()
    checked = prep.check_vector(native, actual["values"])
    assert checked["variables_checked"] == 5728 and checked["rows_checked"] == 14405
    assert str(native.proto) == before
    return {
        "passed": True,
        "variables_checked": 5728,
        "rows_checked": 14405,
        "proto_bytes_unchanged": True,
        "objective_created": False,
        "hint_created": False,
        "model_sha256": prep.sha(model_path),
        "baseline_sha256": prep.sha(prep.BASE),
    }


def main():
    prep = load("prepare")
    partial, cover = synthetic_record(), synthetic_record(True)
    cases = [
        (
            "ordinary-unknown",
            json.dumps({"status": "UNKNOWN", "saved_states": []}),
            {},
            0,
            0,
            "UNKNOWN",
        ),
        (
            "feasible-partial-is-not-cover",
            json.dumps({"status": "OPTIMAL", "saved_states": [partial]}),
            {},
            0,
            0,
            "OPTIMAL",
        ),
        (
            "actual-cover-flag",
            json.dumps({"status": "OPTIMAL", "saved_states": [cover]}),
            {},
            0,
            0,
            "OPTIMAL",
        ),
        (
            "malformed-terminal-recovers-partial",
            '{"unfinished":',
            {"callback-0001-receipt.json": json.dumps(partial)},
            0,
            1,
            "ERROR",
        ),
        (
            "terminate-during-terminal-write",
            '{"unfinished":',
            {
                "callback-0001-receipt.json": json.dumps(partial),
                "callback-0002-receipt.json": '{"unfinished":',
            },
            1,
            -15,
            "WATCHDOG_TIMEOUT",
        ),
        (
            "kill-during-terminal-write",
            '{"unfinished":',
            {"callback-0001-receipt.json": json.dumps(cover)},
            2,
            -9,
            "WATCHDOG_TIMEOUT",
        ),
        ("timeout-without-child-result", None, {}, 1, -15, "WATCHDOG_TIMEOUT"),
    ]
    rows = [run_case(*case) for case in cases]
    result = {
        "passed": True,
        "optimizer_calls": 0,
        "real_child_launches": 0,
        "runner_sha256": prep.sha(HERE / "execute.py"),
        "checker_sha256": prep.sha(Path(__file__)),
        "cases": rows,
        "readonly_vector_validation": check_readonly_vector_validation(),
        "scope": "Synthetic recording-path controls only; no candidate, real process, "
        "solver, cover, or mathematical feasibility result is produced.",
    }
    prep.dump(HERE / "runner-controls.json", result)
    print(
        json.dumps(
            {
                "passed": True,
                "controls": len(rows),
                "optimizer_calls": 0,
                "receipt_sha256": prep.sha(HERE / "runner-controls.json"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
