# Document:    H6 Two-Point Star Repair Preparation Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      7c99bbdd254d60f1ed86d4e61c32626a4d55a3d942b2303a098e55d6a888c01d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Exercise model checks and mocked runner paths without optimization."""

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("h6_star_controlled", HERE / "run.py")
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


def rejected(action):
    try:
        action()
    except (AssertionError, FileExistsError):
        return True
    raise AssertionError("damaged control was accepted")


def main():
    manifest = json.loads((HERE / "manifest.json").read_text())
    model = pilot.read_model(pilot.ROOT / manifest["model"])
    values = json.loads((pilot.RAW / "initial-vector.json").read_text())["values"]
    violations = pilot.violations(model, values)
    assert len(violations) == 3
    controls = {
        "infeasible_initial_vector_rejected": rejected(lambda: pilot.check_vector(model, values))
    }
    relaxed = pilot.read_model(pilot.ROOT / manifest["model"])
    for row in violations:
        relaxed.proto.constraints[row["row"]].linear.domain[0] = 4
    pilot.check_vector(relaxed, values)
    assert pilot.violations(relaxed, values) == []
    controls["only_three_pair_rows_relaxed_accepts_initial"] = True
    for name, replacement in (("bool", True), ("float", 1.0), ("outside_domain", 2)):
        damaged = list(values)
        damaged[0] = replacement
        controls[name] = rejected(lambda: pilot.check_vector(relaxed, damaged))
    controls["short_vector"] = rejected(lambda: pilot.check_vector(relaxed, values[:-1]))
    fixed = next(i for i, b in enumerate(pilot.BLOCKS) if set(b).isdisjoint(pilot.PIVOT))
    damaged = list(values)
    damaged[fixed] = 1 - damaged[fixed]
    controls["flipped_frozen_membership"] = rejected(lambda: pilot.check_vector(relaxed, damaged))
    for name, index in (
        ("hole_marked_covered", values.index(1, 4368)),
        ("covered_marked_hole", values.index(0, 4368)),
    ):
        damaged = list(values)
        damaged[index] = 1 - damaged[index]
        controls[name] = rejected(lambda: pilot.check_vector(relaxed, damaged))
    relaxed.proto.constraints[1241].linear.domain[1] = 5
    controls["hole_cap_five"] = rejected(lambda: pilot.check_vector(relaxed, values))
    params = pilot.cp_model.CpSolver().parameters
    assert params.parse_text_format((pilot.ROOT / manifest["parameters"]).read_text())
    assert str(params) == str(pilot.parameters())
    controls["frozen_parameters_roundtrip"] = True

    with tempfile.TemporaryDirectory(
        prefix="h6-star-controls-", dir=pilot.ROOT / "experiments/scratch"
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
        for key, bad in (("decision", "HOLD"), ("passed", False), ("manifest_sha256", "0" * 64)):
            pilot.dump(gate_path, {**gate, key: bad})
            controls[f"gate_{key}_damage"] = rejected(lambda: pilot.preflight(gate_path))
        pilot.dump(gate_path, gate)
        original_sha = pilot.sha
        with patch.object(
            pilot,
            "sha",
            side_effect=lambda path: (
                "0" * 64 if Path(path) == Path(pilot.__file__) else original_sha(path)
            ),
        ):
            controls["runner_digest_damage"] = rejected(lambda: pilot.preflight(gate_path))

        runner_paths = []
        for name, waits in (
            ("normal", [0]),
            ("terminate", ["timeout", -15]),
            ("kill", ["timeout", "timeout", -9]),
        ):
            root = temp / name
            root.mkdir()
            raw = root / "raw"
            raw.mkdir()
            events = []

            class Process:
                returncode = None

                def wait(self, timeout=None):
                    events.append(["wait", timeout])
                    result = waits.pop(0)
                    if result == "timeout":
                        raise subprocess.TimeoutExpired("mock child", timeout)
                    self.returncode = result
                    return result

                def terminate(self):
                    events.append(["terminate"])

                def kill(self):
                    events.append(["kill"])

            with (
                patch.object(pilot, "HERE", root),
                patch.object(pilot, "RAW", raw),
                patch.object(pilot, "preflight", return_value=manifest),
                patch.object(pilot.subprocess, "Popen", return_value=Process()) as popen,
            ):
                (root / "manifest.json").write_text((HERE / "manifest.json").read_text())
                pilot.execute(gate_path)
                assert popen.call_count == 1
                result = json.loads((root / "result.json").read_text())
                assert result["calls"] == 1 and not result["relaunch"]
                assert result["watchdog_fired"] == (name != "normal")
                assert result["saved"] == [] and not result["cover_found"]
                controls[f"{name}_relaunch_blocked"] = rejected(lambda: pilot.execute(gate_path))
                assert popen.call_count == 1
            expected = {
                "normal": [["wait", 140]],
                "terminate": [["wait", 140], ["terminate"], ["wait", 5]],
                "kill": [["wait", 140], ["terminate"], ["wait", 5], ["kill"], ["wait", None]],
            }[name]
            assert events == expected
            runner_paths.append({"name": name, "events": events, "mock_processes": 1})

        raw = temp / "child-raw"
        output = raw / "run-1"
        output.mkdir(parents=True)
        pilot.dump(
            output / "launch.json",
            {
                "gate_sha256": pilot.sha(gate_path),
                "manifest_sha256": pilot.sha(HERE / "manifest.json"),
            },
        )
        original_solver = pilot.cp_model.CpSolver
        mock_calls = []

        class Solver:
            wall_time = 0.0
            objective_value = 0.0
            best_objective_bound = 0.0
            response_proto = "status: UNKNOWN\n"

            def __init__(self):
                self.parameters = original_solver().parameters

            def solve(self, incoming, collector):
                assert str(incoming.proto) == str(model.proto)
                assert isinstance(collector, pilot.Collector)
                assert str(self.parameters) == str(params)
                mock_calls.append("mock solver only")
                return pilot.cp_model.UNKNOWN

            def status_name(self, status):
                assert status == pilot.cp_model.UNKNOWN
                return "UNKNOWN"

        with patch.object(pilot, "RAW", raw), patch.object(pilot.cp_model, "CpSolver", Solver):
            pilot.child(gate_path)
            controls["second_child_start_blocked"] = rejected(lambda: pilot.child(gate_path))
        assert len(mock_calls) == 1
        outcome = json.loads((output / "outcome.json").read_text())
        assert outcome["status"] == "UNKNOWN" and outcome["callbacks"] == 0
        assert not (output / "final-vector.json").exists()
        controls["unknown_saves_no_solution"] = True

        class Callback(pilot.Collector):
            def value(self, variable):
                return values[variable.index]

        callback = Callback(model, output)
        callback.on_solution_callback()
        saved = json.loads((output / "callback-001.json").read_text())["values"]
        assert saved == values and not list(output.glob("*.tmp"))
        controls["callback_atomic_complete_vector_format"] = True
        controls["infeasible_mock_callback_rejected_on_replay"] = rejected(
            lambda: pilot.check_vector(model, saved)
        )

    report = {
        "passed": True,
        "manifest_sha256": pilot.sha(HERE / "manifest.json"),
        "source_sha256": pilot.sha(__file__),
        "controls": controls,
        "runner_paths": runner_paths,
        "real_optimization_calls": 0,
        "mock_solver_calls": 1,
        "scope": "Preparation controls only. No candidate or feasible start claimed.",
    }
    pilot.dump(HERE / "controls.json", report)
    print(json.dumps({"passed": True, "controls": len(controls), "real_optimization_calls": 0}))


if __name__ == "__main__":
    main()
