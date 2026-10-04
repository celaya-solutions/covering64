# Document:    H6 Two Point Star Warm Repair Preparation Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      b8432694a20fb56c5cdf98f8536920b205072c9d320ff64d21f070348dc8ec59
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Mock process and solver controls only; no optimizer is launched."""

import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from ortools.sat.python import cp_model_helper

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("warm_adapter_controls", HERE / "run.py")
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)
pilot = adapter.runner


def rejected(action):
    try:
        action()
    except (AssertionError, ValueError, FileExistsError):
        return True
    return False


def main():
    manifest = json.loads((HERE / "manifest.json").read_text())
    model = pilot.read_model(adapter.ROOT / manifest["model"])
    values = json.loads((adapter.RAW / "initial-vector.json").read_text())["values"]
    controls = {}
    pilot.check_vector(model, values)
    assert pilot.violations(model, values) == [] and sum(values[4368:]) == 9
    controls["initial_complete_H9_hint_is_feasible"] = True
    old_cap = pilot.read_model(adapter.ROOT / manifest["model"])
    old_cap.proto.constraints[1241].linear.domain[1] = 6
    assert pilot.violations(old_cap, values) == [
        {
            "kind": "linear",
            "row": 1241,
            "amount": 9,
            "domain": [-(2**63), 6],
        }
    ]
    controls["warm_hint_fails_only_old_H6_ceiling"] = True
    controls["short_vector_rejected"] = rejected(lambda: pilot.check_vector(model, values[:4927]))
    for name, index, replacement in [
        ("boolean", 0, True),
        ("float", 0, 0.0),
        ("outside_domain", 0, 2),
        ("hole_marked_covered", 4368 + values[4368:].index(1), 0),
        ("covered_marked_hole", 4368 + values[4368:].index(0), 1),
    ]:
        damaged = list(values)
        damaged[index] = replacement
        controls[name] = rejected(lambda: pilot.check_vector(model, damaged))
    fixed = next(i for i, b in enumerate(pilot.BLOCKS) if not set(adapter.PIVOT).intersection(b))
    damaged = list(values)
    damaged[fixed] = 1 - damaged[fixed]
    controls["flipped_outside_membership_rejected"] = rejected(
        lambda: pilot.check_vector(model, damaged)
    )
    assert str(pilot.parameters()) == (adapter.RAW / "parameters.pbtxt").read_text()
    controls["parameters_seed6002_exact"] = True
    assert pilot.__file__ == str(HERE / "run.py")
    assert pilot.child.__code__.co_filename == str(adapter.BASE_RUNNER)
    assert pilot.execute.__code__.co_filename == str(adapter.BASE_RUNNER)
    assert pilot.preflight.__code__.co_filename == str(adapter.BASE_RUNNER)
    controls["runner_function_bodies_reused_unchanged"] = True
    traces = []
    mock_solves = []
    with tempfile.TemporaryDirectory(
        prefix="h6-warm-controls-", dir=adapter.ROOT / "experiments/scratch"
    ) as temporary:
        temp = Path(temporary)
        gate_path = temp / "gate.json"
        gate = {
            "decision": "GO",
            "passed": True,
            "manifest_sha256": pilot.sha(HERE / "manifest.json"),
        }
        pilot.dump(gate_path, gate)
        assert pilot.preflight(gate_path) == manifest
        controls["valid_gate_preflight_only"] = True
        for key, value in [("decision", "HOLD"), ("passed", False), ("manifest_sha256", "0" * 64)]:
            pilot.dump(gate_path, {**gate, key: value})
            controls[f"damaged_gate_{key}"] = rejected(lambda: pilot.preflight(gate_path))
        pilot.dump(gate_path, gate)
        original_sha = pilot.sha
        with patch.object(
            pilot,
            "sha",
            side_effect=lambda p: "0" * 64 if Path(p) == HERE / "run.py" else original_sha(p),
        ):
            controls["adapter_digest_damage_rejected"] = rejected(
                lambda: pilot.preflight(gate_path)
            )
        with patch.object(
            pilot,
            "sha",
            side_effect=lambda p: "0" * 64 if Path(p) == adapter.BASE_RUNNER else original_sha(p),
        ):
            controls["base_runner_digest_damage_rejected"] = rejected(
                lambda: pilot.preflight(gate_path)
            )

        for name, waits in [
            ("normal", [0]),
            ("terminate", [None, -15]),
            ("kill", [None, None, -9]),
        ]:
            root = temp / name
            raw = root / "raw"
            raw.mkdir(parents=True)
            (root / "manifest.json").write_bytes((HERE / "manifest.json").read_bytes())
            events = []

            class Process:
                returncode = None

                def wait(self, timeout=None):
                    events.append(["wait", timeout])
                    returned = waits.pop(0)
                    if returned is None:
                        raise subprocess.TimeoutExpired("mock child", timeout)
                    self.returncode = returned

                def terminate(self):
                    events.append(["terminate"])

                def kill(self):
                    events.append(["kill"])

            with (
                patch.object(pilot, "HERE", root),
                patch.object(pilot, "RAW", raw),
                patch.object(pilot, "preflight", return_value=manifest),
                patch.object(pilot.subprocess, "Popen", return_value=Process()) as popen,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                pilot.execute(gate_path)
                assert popen.call_count == 1
                command = popen.call_args.args[0]
                assert command[1:] == [str(HERE / "run.py"), "--child", str(gate_path)]
                controls[f"{name}_relaunch_blocked"] = rejected(lambda: pilot.execute(gate_path))
                assert popen.call_count == 1
            result = json.loads((root / "result.json").read_text())
            assert result["calls"] == 1 and result["relaunch"] is False
            assert not result["saved"] and result["cover_found"] is False
            assert result["watchdog_fired"] is (name != "normal")
            expected = {
                "normal": [["wait", 140]],
                "terminate": [["wait", 140], ["terminate"], ["wait", 5]],
                "kill": [["wait", 140], ["terminate"], ["wait", 5], ["kill"], ["wait", None]],
            }[name]
            assert events == expected
            traces.append({"case": name, "events": events, "mock_processes": 1})

        original_solver = pilot.cp_model.CpSolver
        for name, status in [
            ("unknown", pilot.cp_model.UNKNOWN),
            ("feasible", pilot.cp_model.FEASIBLE),
        ]:
            raw = temp / name
            output = raw / "run-1"
            output.mkdir(parents=True)
            pilot.dump(
                output / "launch.json",
                {
                    "gate_sha256": pilot.sha(gate_path),
                    "manifest_sha256": pilot.sha(HERE / "manifest.json"),
                },
            )

            class Solver:
                wall_time = 0.0
                objective_value = 9.0
                best_objective_bound = 0.0

                def __init__(self):
                    self.parameters = original_solver().parameters
                    self.response_proto = cp_model_helper.CpSolverResponse()
                    self.response_proto.status = status
                    self.response_proto.objective_value = 9
                    if status == pilot.cp_model.FEASIBLE:
                        self.response_proto.solution.extend(values)

                def solve(self, incoming, collector):
                    assert str(incoming.proto) == str(model.proto)
                    assert isinstance(collector, pilot.Collector)
                    assert str(self.parameters) == str(pilot.parameters())
                    mock_solves.append(name)
                    return status

                def status_name(self, returned):
                    assert returned == status
                    return name.upper()

            with patch.object(pilot, "RAW", raw), patch.object(pilot.cp_model, "CpSolver", Solver):
                pilot.child(gate_path)
                controls[f"{name}_duplicate_child_rejected"] = rejected(
                    lambda: pilot.child(gate_path)
                )
            final = output / "final-vector.json"
            if name == "unknown":
                assert not final.exists()
                controls["unknown_is_not_a_solution"] = True
            else:
                assert json.loads(final.read_text())["values"] == values
                pilot.check_vector(model, values)
                controls["feasible_mock_saves_complete_vector"] = True

        class Callback(pilot.Collector):
            def value(self, variable):
                return values[variable.index]

        callback_output = temp / "callback"
        callback_output.mkdir()
        callback = Callback(model, callback_output)
        callback.on_solution_callback()
        saved = json.loads((callback_output / "callback-001.json").read_text())["values"]
        assert saved == values and not list(callback_output.glob("*.tmp"))
        pilot.check_vector(model, saved)
        controls["feasible_callback_atomic_complete_vector"] = True
    assert all(controls.values()) and mock_solves == ["unknown", "feasible"]
    report = {
        "passed": True,
        "manifest_sha256": pilot.sha(HERE / "manifest.json"),
        "source_sha256": pilot.sha(__file__),
        "controls": controls,
        "runner_paths": traces,
        "real_optimization_calls": 0,
        "real_native_processes": 0,
        "mock_solver_calls": 2,
        "scope": "Preparation controls only. Feasible H9 hint, no optimization or production run.",
    }
    assert not (HERE / "controls.json").exists()
    pilot.dump(HERE / "controls.json", report)
    print(json.dumps({"passed": True, "controls": len(controls), "real_optimization_calls": 0}))


if __name__ == "__main__":
    main()
