# Document:    Independent H6 Star Warm Continuation Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      fcc2a20dd49dde63b8db2f9083f0d6ebc666c0b4410e58d76e57ca59ff0d625f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check full serialized models, real hint, and mocked dispatch; never solve."""

import hashlib
import importlib.util
import itertools
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

from covering64.core import verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "h6-two-point-star-warm-repair"
MANIFEST_SHA = "b2ddc08cc5cd816046b2e49621bcc475c9d60b99c61ed7d7b266b28553d584d1"
OLD = ROOT / "experiments/scratch/h6-two-point-star-repair-20261004"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
TRIPLES = list(itertools.combinations(range(1, 17), 3))
PAIRS = list(itertools.combinations(range(1, 17), 2))
MIN, MAX = -(2**63), 2**63 - 1


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def proto(path):
    result = cp_model_pb2.CpModelProto()
    text_format.Parse(Path(path).read_text(), result)
    return result


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reject(action):
    try:
        action()
    except AssertionError:
        return True
    raise AssertionError("damaged control accepted")


def check_vector(model, values):
    assert len(values) == len(model.variables) and all(type(v) is int for v in values)
    for variable, value in zip(model.variables, values):
        domain = list(variable.domain)
        assert any(a <= value <= b for a, b in zip(domain[::2], domain[1::2]))
    for row in model.constraints:
        if not all(values[i] if i >= 0 else not values[-i - 1] for i in row.enforcement_literal):
            continue
        assert row.WhichOneof("constraint") == "linear"
        amount = sum(values[i] * c for i, c in zip(row.linear.vars, row.linear.coeffs))
        domain = list(row.linear.domain)
        assert any(a <= amount <= b for a, b in zip(domain[::2], domain[1::2]))


def main():
    manifest_path = PRODUCER / "manifest.json"
    assert sha(manifest_path) == MANIFEST_SHA
    manifest = json.loads(manifest_path.read_text())
    pins = {
        **manifest["dependencies"],
        **manifest["prepared_files"],
        str((PRODUCER / "run.py").relative_to(ROOT)): manifest["source_sha256"],
    }
    for name, digest in pins.items():
        assert sha(ROOT / name) == digest, name
    original, model = proto(OLD / "model.pbtxt"), proto(ROOT / manifest["model"])
    start = HERE.parent / "h6-anchored-pair-repair/candidate-02.txt"
    blocks = [tuple(map(int, line.split())) for line in start.read_text().splitlines()]
    assert blocks == sorted(set(blocks)) and len(blocks) == 64
    chosen = {BLOCKS.index(b) for b in blocks}
    triple_counts = Counter(t for b in blocks for t in itertools.combinations(b, 3))
    pair_counts = Counter(p for b in blocks for p in itertools.combinations(b, 2))
    values = [int(i in chosen) for i in range(4368)]
    values += [int(triple_counts[t] == 0) for t in TRIPLES]
    old_values = json.loads((OLD / "initial-vector.json").read_text())["values"]
    assert sum(values[:4368]) == 64 and sum(values[4368:]) == 9
    assert min(pair_counts[p] for p in PAIRS) == 5
    outside = [i for i, b in enumerate(BLOCKS) if {6, 10}.isdisjoint(b)]
    assert len(outside) == 2002 and sum(values[i] for i in outside) == 30
    assert all(values[i] == old_values[i] for i in outside)
    changed = [i for i in range(4368) if values[i] != old_values[i]]
    assert changed == [2859, 3054, 3106, 4075]

    def model_check(incoming):
        assert len(incoming.variables) == 4928 and len(incoming.constraints) == 1242
        assert list(incoming.constraints[1241].linear.domain) == [MIN, 9]
        assert list(incoming.solution_hint.vars) == list(original.solution_hint.vars)
        assert len(incoming.solution_hint.vars) == len(set(incoming.solution_hint.vars)) == 4928
        assert list(incoming.solution_hint.values) == [
            values[i] for i in incoming.solution_hint.vars
        ]
        restored = cp_model_pb2.CpModelProto()
        restored.CopyFrom(incoming)
        restored.constraints[1241].linear.domain[1] = 6
        restored.solution_hint.CopyFrom(original.solution_hint)
        assert restored.SerializeToString(deterministic=True) == original.SerializeToString(
            deterministic=True
        )
        check_vector(incoming, values)

    model_check(model)
    for i, variable in enumerate(model.variables):
        name = f"b_{i}" if i < 4368 else f"h_{i - 4368}"
        expected = [old_values[i], old_values[i]] if i in outside else [0, 1]
        assert variable.name == name and list(variable.domain) == expected

    def linear(index, indices, domain, enforcement=()):
        row = model.constraints[index]
        assert row.WhichOneof("constraint") == "linear" and not row.name
        assert list(row.enforcement_literal) == list(enforcement)
        assert list(row.linear.vars) == indices and list(row.linear.coeffs) == [1] * len(indices)
        assert list(row.linear.domain) == domain

    linear(0, list(range(4368)), [64, 64])
    for j, triple in enumerate(TRIPLES):
        ids = [i for i, b in enumerate(BLOCKS) if set(triple) <= set(b)]
        linear(1 + 2 * j, ids, [0, 0], [4368 + j])
        linear(2 + 2 * j, ids, [1, MAX], [-(4368 + j) - 1])
    for j, pair in enumerate(PAIRS):
        ids = [i for i, b in enumerate(BLOCKS) if set(pair) <= set(b)]
        linear(1121 + j, ids, [5, MAX])
    linear(1241, list(range(4368, 4928)), [MIN, 9])
    assert list(model.objective.vars) == list(range(4368, 4928))
    assert list(model.objective.coeffs) == [1] * 560
    assert model.objective.offset == 0 and model.objective.scaling_factor == 1

    parameter = sat_parameters_pb2.SatParameters()
    text_format.Parse((ROOT / manifest["parameters"]).read_text(), parameter)
    expected_parameter = sat_parameters_pb2.SatParameters(
        max_time_in_seconds=120,
        num_search_workers=4,
        random_seed=2026106002,
        log_search_progress=True,
    )
    assert parameter == expected_parameter
    parameter.random_seed = 2026106001
    old_parameter = sat_parameters_pb2.SatParameters()
    text_format.Parse((OLD / "parameters.pbtxt").read_text(), old_parameter)
    assert parameter == old_parameter
    controls = {}
    for name in (
        "domain",
        "cardinality",
        "hole_enforcement",
        "pair_floor",
        "objective",
        "cap",
        "hint",
    ):
        damaged = cp_model_pb2.CpModelProto()
        damaged.CopyFrom(model)
        if name == "domain":
            damaged.variables[0].domain[:] = [0, 1]
        elif name == "cardinality":
            damaged.constraints[0].linear.domain[:] = [65, 65]
        elif name == "hole_enforcement":
            damaged.constraints[1].enforcement_literal[0] = 4369
        elif name == "pair_floor":
            damaged.constraints[1121].linear.domain[0] = 4
        elif name == "objective":
            damaged.objective.coeffs[0] = 2
        elif name == "cap":
            damaged.constraints[1241].linear.domain[1] = 10
        else:
            damaged.solution_hint.values[0] = 1 - damaged.solution_hint.values[0]
        controls[name] = reject(lambda: model_check(damaged))
    for name, replacement in (("bool_vector", True), ("float_vector", 0.0), ("invalid_domain", 2)):
        damaged_values = list(values)
        damaged_values[0] = replacement
        controls[name] = reject(lambda: check_vector(model, damaged_values))
    damaged_values = list(values)
    damaged_values[4368] = 1 - damaged_values[4368]
    controls["false_hole"] = reject(lambda: check_vector(model, damaged_values))
    controls["short_vector"] = reject(lambda: check_vector(model, values[:-1]))
    package = verify_cover(blocks)
    verified = subprocess.run(
        [sys.executable, "scripts/check_cover.py", str(start), "--expected-blocks", "64"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    standalone = json.loads(verified.stdout)
    assert verified.returncode == 1 and not verified.stderr
    assert package["valid"] is False and len(package["uncovered"]) == 9
    assert standalone["valid"] is False and standalone["uncovered_count"] == 9
    assert standalone["cardinality_matches"] and standalone["blocks"] == 64

    adapter = load(PRODUCER / "run.py", "warm_star_independent_adapter")
    runner = adapter.runner
    pristine = load(ROOT / manifest["base_runner_path"], "warm_star_pristine_runner")
    for name in ("preflight", "parameters", "child", "execute", "violations", "build"):
        assert getattr(runner, name).__code__ == getattr(pristine, name).__code__, name
    assert runner.HERE == PRODUCER and runner.RAW == adapter.RAW
    assert runner.BASE == start and runner.BASE_SHA == sha(start)
    assert runner.SEED == 2026106002 and runner.REVISION == manifest["source_revision"]
    assert Path(runner.__file__) == PRODUCER / "run.py"
    assert runner.ROOT == ROOT and runner.PIVOT == (6, 10)
    traces = []
    with tempfile.TemporaryDirectory(
        prefix="warm-star-independent-", dir=ROOT / "experiments/scratch"
    ) as temp:
        temp = Path(temp)
        gate_path = temp / "gate.json"
        dump(gate_path, {"decision": "GO", "passed": True, "manifest_sha256": MANIFEST_SHA})
        assert runner.preflight(gate_path) == manifest
        for name, responses in (
            ("normal", [0]),
            ("terminate", [None, -15]),
            ("kill", [None, None, -9]),
        ):
            folder = temp / name
            raw = folder / "raw"
            raw.mkdir(parents=True)
            (folder / "manifest.json").write_bytes(manifest_path.read_bytes())
            events = []

            class Process:
                returncode = None

                def wait(self, timeout=None):
                    events.append(["wait", timeout])
                    response = responses.pop(0)
                    if response is None:
                        raise subprocess.TimeoutExpired("mock", timeout)
                    self.returncode = response

                def terminate(self):
                    events.append(["terminate"])

                def kill(self):
                    events.append(["kill"])

            with (
                patch.object(runner, "HERE", folder),
                patch.object(runner, "RAW", raw),
                patch.object(runner.subprocess, "Popen", return_value=Process()) as mocked,
            ):
                runner.execute(gate_path)
                assert mocked.call_count == 1
                command = mocked.call_args.args[0]
                assert Path(command[1]) == PRODUCER / "run.py" and command[2:] == [
                    "--child",
                    str(gate_path),
                ]
                controls[f"{name}_relaunch"] = reject(lambda: runner.execute(gate_path))
                assert mocked.call_count == 1
            expected_events = {
                "normal": [["wait", 140]],
                "terminate": [["wait", 140], ["terminate"], ["wait", 5]],
                "kill": [["wait", 140], ["terminate"], ["wait", 5], ["kill"], ["wait", None]],
            }[name]
            assert events == expected_events
            traces.append({"name": name, "events": events, "adapter_child_dispatch": True})

    previous_path = HERE.parent / "h6-two-point-star-repair/result.json"
    previous = json.loads(previous_path.read_text())
    assert previous["outcome"]["status"] == "UNKNOWN" and previous["outcome"]["callbacks"] == 0
    assert previous["saved"] == [] and not previous["cover_found"]
    assert not (adapter.RAW / "run-1").exists() and not (PRODUCER / "result.json").exists()
    report = {
        "passed": True,
        "manifest_sha256": MANIFEST_SHA,
        "checker_sha256": sha(__file__),
        "pins_verified": len(pins),
        "variables": 4928,
        "rows": 1242,
        "only_constraint_delta": {"row": 1241, "old_cap": 6, "new_cap": 9},
        "changed_hint_values": sum(
            a != b for a, b in zip(original.solution_hint.values, model.solution_hint.values)
        ),
        "hint_feasible": True,
        "hint_holes": 9,
        "pair_floor": 5,
        "outside_memberships_preserved": 2002,
        "outside_selected": 30,
        "changed_block_ids": changed,
        "parameter_delta_only_seed": [2026106001, 2026106002],
        "controls": controls,
        "mock_watchdog_traces": traces,
        "package": package,
        "standalone": standalone,
        "previous_unknown": {
            "result_sha256": sha(previous_path),
            "saved_candidates": 0,
            "reported_objective": previous["outcome"]["objective"],
            "objective_is_incumbent": False,
        },
        "real_solver_calls": 0,
        "real_native_launches": 0,
        "scope": "Same fixed star, feasible H9 hint and H<=9. Prior UNKNOWN objective 6 is "
        "not an incumbent. One 120s four-worker call, seed 2026106002, "
        "140s watchdog plus 5s grace; root owns launch.",
    }
    dump(HERE / "review.json", report)
    dump(
        HERE / "gate.json",
        {
            "decision": "GO",
            "passed": True,
            "manifest_sha256": MANIFEST_SHA,
            "review_sha256": sha(HERE / "review.json"),
            "checker_sha256": sha(__file__),
            "scope": report["scope"],
            "real_solver_calls_during_review": 0,
        },
    )
    print(
        json.dumps(
            {
                "passed": True,
                "gate_sha256": sha(HERE / "gate.json"),
                "review_sha256": sha(HERE / "review.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
