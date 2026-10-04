# Document:    Independent Eight by Eight Extension Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      92fce97757c4ce0865a6a0a5975d11308a299a98a1b0605e1c6c9e2841efeaa5
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Reconstruct frozen models and test control flow without launching a solver."""

import contextlib
import copy
import hashlib
import importlib.util
import io
import itertools
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import ortools
from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "eight-eight-extensions/run.py"
MANIFEST_PATH = PRODUCER.with_name("manifest.json")
SPEC = importlib.util.spec_from_file_location("frozen_extensions", PRODUCER)
RUN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN)
COMMON = RUN.COMMON
BLOCKS = list(itertools.combinations(range(1, 17), 5))
TRIPLES = list(itertools.combinations(range(1, 17), 3))
SUPPORTS = [[i for i, b in enumerate(BLOCKS) if set(t).issubset(b)] for t in TRIPLES]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def rejects(call):
    try:
        call()
    except (AssertionError, ValueError, TypeError, KeyError, IndexError):
        return True
    raise AssertionError("Damage was accepted")


def independent_groups(kinds):
    groups = []
    for half, kind in enumerate(kinds):
        points = set(range(8 * half + 1, 8 * half + 9))
        excluded = ((1, 0, 0), (0, 1, 0), (1, 1, 0) if kind == "A" else (0, 0, 1))
        normals = [v for v in itertools.product((0, 1), repeat=3) if any(v) and v not in excluded]
        quads = []
        for normal in normals:
            for parity in (0, 1):
                quad = tuple(
                    p
                    for p in sorted(points)
                    if sum(((p - 1 - 8 * half) // (2**j) % 2) * normal[j] for j in range(3)) % 2
                    == parity
                )
                quads.append(quad)
        covered = [t for q in quads for t in itertools.combinations(q, 3)]
        assert len(quads) == 8 and len(set(covered)) == 32
        assert all(sum(p in q for q in quads) == 4 for p in points)
        bases = sorted(
            quads + [t for t in itertools.combinations(sorted(points), 3) if t not in covered]
        )
        assert len(bases) == 32
        for base in bases:
            ids = [
                i
                for i, block in enumerate(BLOCKS)
                if tuple(p for p in block if p in points) == base
            ]
            assert len(ids) == (8 if len(base) == 4 else 28)
            groups.append({"base": list(base), "ids": ids})
    return groups


def expected_proto(groups):
    allowed = {i for group in groups for i in group["ids"]}
    assert len(groups) == 64 and len(allowed) == 1472
    assert sum(len(g["ids"]) for g in groups) == 1472
    proto = cp_model_pb2.CpModelProto()
    for i in range(len(BLOCKS)):
        v = proto.variables.add(name=f"b_{i}")
        v.domain.extend([0, 1 if i in allowed else 0])
    rows = [(list(range(len(BLOCKS))), [64, 64])]
    rows += [(g["ids"], [1, 1]) for g in groups]
    rows += [(s, [1, (1 << 63) - 1]) for s in SUPPORTS]
    for support, domain in rows:
        row = proto.constraints.add().linear
        row.vars.extend(support)
        row.coeffs.extend([1] * len(support))
        row.domain.extend(domain)
    return proto


def audit_proto(proto, groups, kinds):
    expected_groups = independent_groups(kinds)
    assert groups == expected_groups
    assert proto == expected_proto(expected_groups)


def damaged_model_controls(proto, groups, kinds):
    allowed = {i for g in groups for i in g["ids"]}
    forbidden = next(i for i in range(len(BLOCKS)) if i not in allowed)
    eligible = min(allowed)
    outside_first_triple = next(i for i in range(len(BLOCKS)) if i not in SUPPORTS[0])
    controls = {}
    operations = {
        "free_forbidden": lambda p: p.variables[forbidden].domain.__setitem__(1, 1),
        "fix_eligible": lambda p: p.variables[eligible].domain.__setitem__(1, 0),
        "rename_variable": lambda p: setattr(p.variables[0], "name", "wrong"),
        "cardinality_lower": lambda p: p.constraints[0].linear.domain.__setitem__(0, 63),
        "cardinality_support": lambda p: p.constraints[0].linear.vars.pop(),
        "group_support": lambda p: p.constraints[1].linear.vars.__setitem__(0, forbidden),
        "group_bound": lambda p: p.constraints[1].linear.domain.__setitem__(1, 2),
        "coverage_support": lambda p: p.constraints[65].linear.vars.__setitem__(
            0, outside_first_triple
        ),
        "coverage_coefficient": lambda p: p.constraints[65].linear.coeffs.__setitem__(0, 2),
        "coverage_bound": lambda p: p.constraints[65].linear.domain.__setitem__(0, 0),
        "remove_cover_row": lambda p: p.constraints.pop(),
        "enforcement_literal": lambda p: p.constraints[65].enforcement_literal.append(eligible),
        "add_objective": lambda p: p.objective.vars.append(eligible),
        "add_hint": lambda p: p.solution_hint.vars.append(eligible),
        "add_variable": lambda p: p.variables.add(name="aux"),
        "add_constraint": lambda p: p.constraints.add().bool_or.literals.append(eligible),
    }
    for name, operation in operations.items():
        damaged = copy.deepcopy(proto)
        operation(damaged)
        assert damaged != proto, name
        controls[name] = rejects(lambda: audit_proto(damaged, groups, kinds))
    for name in ("base", "id", "duplicate", "remove"):
        damaged = copy.deepcopy(groups)
        if name == "base":
            damaged[0]["base"][0] = 16
        elif name == "id":
            damaged[0]["ids"][0] = forbidden
        elif name == "duplicate":
            damaged.append(copy.deepcopy(damaged[0]))
        else:
            damaged.pop()
        controls[f"group_json_{name}"] = rejects(lambda: audit_proto(proto, damaged, kinds))
    return controls


def fake_child_controls(manifest):
    results = []
    for entry in manifest["entries"]:
        for status in (cp_model.UNKNOWN, cp_model.FEASIBLE):
            calls = []

            class FakeSolver:
                def __init__(self):
                    self.parameters = sat_parameters_pb2.SatParameters()
                    self.response_proto = SimpleNamespace(solution=[0] * len(BLOCKS))
                    self.wall_time = 0.001

                def solve(self, model, collector):
                    calls.append(
                        {
                            "seconds": self.parameters.max_time_in_seconds,
                            "workers": self.parameters.num_search_workers,
                            "seed": self.parameters.random_seed,
                            "logging": self.parameters.log_search_progress,
                            "variables": len(collector.variables),
                        }
                    )
                    assert len(model.proto.variables) == len(BLOCKS)
                    return status

                def status_name(self, value):
                    return "FEASIBLE" if value == cp_model.FEASIBLE else "UNKNOWN"

            with tempfile.TemporaryDirectory(dir=HERE) as temporary:
                raw = Path(temporary)
                output = raw / f"run-{entry['number']}"
                output.mkdir()
                with patch.object(RUN, "RAW", raw), patch.object(cp_model, "CpSolver", FakeSolver):
                    RUN.child(entry["number"])
                assert calls == [
                    {
                        "seconds": 120.0,
                        "workers": 4,
                        "seed": entry["seed"],
                        "logging": True,
                        "variables": 4368,
                    }
                ]
                outcome = json.loads((output / "outcome.json").read_text())
                assert outcome["callbacks"] == 0
                assert (output / "final-vector.json").exists() == (status == cp_model.FEASIBLE)
                if status == cp_model.FEASIBLE:
                    assert (
                        len(json.loads((output / "final-vector.json").read_text())["values"])
                        == 4368
                    )
                results.append(
                    {
                        "number": entry["number"],
                        "status": outcome["status"],
                        "calls": calls,
                        "synthetic_values_not_a_candidate": True,
                    }
                )
    return results


def fake_execute_control(manifest, scenario):
    calls, waits, signals, checked = [], [], [], []
    with tempfile.TemporaryDirectory(dir=HERE) as temporary:
        root = Path(temporary)
        here, raw = root / "prepared", root / "raw"
        here.mkdir()
        raw.mkdir()
        shutil.copyfile(MANIFEST_PATH, here / "manifest.json")
        gate = root / "gate.json"
        dump(gate, {"passed": True, "decision": "GO", "manifest_sha256": sha(MANIFEST_PATH)})
        for entry in manifest["entries"]:
            for field in ("model", "groups"):
                target = root / entry[field]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / entry[field], target)

        if scenario.startswith("preflight_"):
            damage = scenario.removeprefix("preflight_")
            gate_value = json.loads(gate.read_text())
            if damage == "decision":
                gate_value["decision"] = "NO GO"
            elif damage == "passed":
                gate_value["passed"] = False
            elif damage == "manifest":
                gate_value["manifest_sha256"] = "wrong"
            elif damage in ("source", "common"):
                changed = copy.deepcopy(manifest)
                changed[f"{damage}_sha256"] = "wrong"
                dump(here / "manifest.json", changed)
                gate_value["manifest_sha256"] = sha(here / "manifest.json")
            elif damage in ("model", "groups"):
                (root / manifest["entries"][0][damage]).write_text("damaged")
            elif damage == "raw":
                (raw / "run-prior").mkdir()
            elif damage == "result":
                dump(here / "result.json", {})
            else:
                raise AssertionError(damage)
            dump(gate, gate_value)

        class FakeProcess:
            def __init__(self, command, cwd, stdout, stderr):
                assert cwd == root
                number = int(command[-1])
                assert command[-2] == "--child" and Path(command[1]) == PRODUCER
                calls.append(number)
                self.returncode = 7 if scenario == "error" else 0
                self.wait_count = 0
                output = raw / f"run-{number}"
                if scenario != "missing":
                    dump(output / "outcome.json", {"status": "UNKNOWN", "callbacks": 0})
                if scenario == "vector":
                    dump(output / "callback-001.json", {"values": [1] + [0] * 4367})
                if scenario == "bad_vector":
                    dump(output / "callback-001.json", {"values": [0] * 4368})
                if scenario == "partial_atomic":
                    (output / "callback-001.json.tmp").write_text('{"values":')

            def wait(self, timeout=None):
                waits.append(timeout)
                self.wait_count += 1
                if scenario in ("timeout", "kill") and self.wait_count == 1:
                    raise subprocess.TimeoutExpired("fake", timeout)
                if scenario == "kill" and self.wait_count == 2:
                    raise subprocess.TimeoutExpired("fake", timeout)
                return self.returncode

            def terminate(self):
                signals.append("terminate")

            def kill(self):
                signals.append("kill")

        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(RUN, "ROOT", root))
            stack.enter_context(patch.object(RUN, "HERE", here))
            stack.enter_context(patch.object(RUN, "RAW", raw))
            stack.enter_context(patch.object(subprocess, "Popen", FakeProcess))
            if scenario.startswith("preflight_"):
                assert rejects(lambda: RUN.execute(gate))
                assert calls == []
                return {"scenario": scenario, "rejected_before_launch": True}
            if scenario == "vector":
                stack.enter_context(
                    patch.object(COMMON, "check_vector", lambda m, v: checked.append(v))
                )
                stack.enter_context(patch.object(COMMON, "dual", lambda p: [{"valid": True}] * 2))
            with contextlib.redirect_stdout(io.StringIO()):
                if scenario == "bad_vector":
                    assert rejects(lambda: RUN.execute(gate))
                    assert not (here / "cover.txt").exists()
                    return {"scenario": scenario, "calls": calls, "rejected": True}
                RUN.execute(gate)
                result = json.loads((here / "result.json").read_text())
                assert rejects(lambda: RUN.execute(gate))
            expected_runs = 3 if scenario in ("unknown", "partial_atomic") else 1
            assert calls == list(range(1, expected_runs + 1))
            assert result["relaunch"] is False and len(result["runs"]) == expected_runs
            assert result["cover_found"] == (scenario == "vector")
            assert signals == (
                {"timeout": ["terminate"], "kill": ["terminate", "kill"]}.get(scenario, [])
            )
            if scenario in ("timeout", "kill"):
                assert waits == ([145, 5] if scenario == "timeout" else [145, 5, None])
                assert result["runs"][0]["watchdog_fired"]
            else:
                assert waits == [145] * expected_runs
            if scenario == "vector":
                assert len(checked) == 1 and (here / "cover.txt").exists()
            return {
                "scenario": scenario,
                "calls": calls,
                "waits": waits,
                "signals": signals,
                "relaunch_rejected": True,
                "synthetic_vector_branch_only": scenario == "vector",
            }


def actual_positive_and_callback():
    """A full ordinary cover exercises helpers; it is outside every64 recipe."""
    folder = HERE / "positive-control"
    folder.mkdir(exist_ok=True)
    witness = folder / "ordinary-4368.txt"
    witness.write_text(COMMON.family(list(range(len(BLOCKS)))))
    assert witness.read_text() == "".join(" ".join(map(str, b)) + "\n" for b in BLOCKS)
    proto = cp_model_pb2.CpModelProto()
    for i in range(len(BLOCKS)):
        proto.variables.add(name=f"b_{i}").domain.extend([0, 1])
    for support in SUPPORTS:
        row = proto.constraints.add().linear
        row.vars.extend(support)
        row.coeffs.extend([1] * len(support))
        row.domain.extend([1, (1 << 63) - 1])
    model_path = folder / "ordinary.pbtxt"
    model_path.write_text(text_format.MessageToString(proto))
    model = COMMON.read_model(model_path)
    assert not model.validate()
    values = [1] * len(BLOCKS)
    COMMON.check_vector(model, values)
    damages = {
        "short": values[:4367],
        "long": values + [0],
        "boolean": [True] + values[1:],
        "float": [1.0] + values[1:],
        "out_of_domain": [2] + values[1:],
        "uncovered": [0] * len(BLOCKS),
    }
    controls = {
        name: rejects(lambda v=v: COMMON.check_vector(model, v)) for name, v in damages.items()
    }
    stop_calls = []
    callback = SimpleNamespace(
        variables=list(range(len(BLOCKS))),
        count=0,
        output=folder,
        value=lambda i: values[i],
        stop_search=lambda: stop_calls.append(1),
    )
    COMMON.Collector.on_solution_callback(callback)
    assert callback.count == 1 and stop_calls == [1]
    assert json.loads((folder / "callback-001.json").read_text())["values"] == values
    assert not list(folder.glob("*.tmp"))
    receipts = []
    for prefix in (
        ["uv", "run", "covering64", "verify"],
        [sys.executable, "scripts/check_cover.py"],
    ):
        command = [*prefix, str(witness), "--expected-blocks", "4368"]
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        parsed = json.loads(process.stdout)
        assert process.returncode == 0 and parsed["valid"] and parsed["uncovered"] == []
        assert parsed["blocks"] == 4368
        receipts.append({"command": command, "returncode": process.returncode, "result": parsed})
    assert receipts[0]["result"]["canonical_sha256"] == receipts[1]["result"]["canonical_sha256"]
    # The temporary ordinary model is large and fully reconstructible from this audit.
    model_hash = sha(model_path)
    model_path.unlink()
    return {
        "scope": "Known ordinary4368-cover; not a feasible restricted64-vector",
        "witness_sha256": sha(witness),
        "ordinary_model_sha256": model_hash,
        "verifiers": receipts,
        "vector_damage_controls": controls,
        "callback_full_values": 4368,
        "callback_stop_calls": 1,
        "callback_scope": "Synthetic callback API exercise with a real ordinary cover",
    }


def main():
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert sha(PRODUCER) == manifest["source_sha256"]
    assert sha(RUN.COMMON_PATH) == manifest["common_sha256"]
    assert manifest["ortools_version"] == ortools.__version__ == "9.15.6755"
    assert (manifest["seconds"], manifest["workers"], manifest["watchdog"], manifest["grace"]) == (
        120,
        4,
        145,
        5,
    )
    assert [e["kinds"] for e in manifest["entries"]] == ["AA", "AB", "BB"]
    assert [e["seed"] for e in manifest["entries"]] == [2026105401, 2026105402, 2026105403]
    assert manifest["search_launches_during_preparation"] == 0
    model_receipts = []
    # Every call to the real solver would fail immediately, including accidental calls.
    with patch.object(
        cp_model.CpSolver, "solve", side_effect=AssertionError("Solver launch forbidden")
    ):
        for entry in manifest["entries"]:
            model_path, group_path = ROOT / entry["model"], ROOT / entry["groups"]
            assert sha(model_path) == entry["model_sha256"]
            assert sha(group_path) == entry["groups_sha256"]
            proto = text_format.Parse(model_path.read_text(), cp_model_pb2.CpModelProto())
            groups = json.loads(group_path.read_text())
            audit_proto(proto, groups, entry["kinds"])
            model = COMMON.read_model(model_path)
            assert not model.validate()
            controls = damaged_model_controls(proto, groups, entry["kinds"])
            model_receipts.append(
                {
                    "kinds": entry["kinds"],
                    "variables": len(proto.variables),
                    "rows": len(proto.constraints),
                    "eligible": 1472,
                    "coverage_support_size": sorted({len(s) for s in SUPPORTS}),
                    "native_validation": "passed",
                    "damage_controls": controls,
                    "model_sha256": sha(model_path),
                    "groups_sha256": sha(group_path),
                }
            )
        children = fake_child_controls(manifest)
        runners = [
            fake_execute_control(manifest, scenario)
            for scenario in (
                "unknown",
                "timeout",
                "kill",
                "error",
                "missing",
                "vector",
                "bad_vector",
                "partial_atomic",
                "preflight_decision",
                "preflight_passed",
                "preflight_manifest",
                "preflight_source",
                "preflight_common",
                "preflight_model",
                "preflight_groups",
                "preflight_raw",
                "preflight_result",
            )
        ]
        positive = actual_positive_and_callback()
    result = {
        "passed": True,
        "manifest_sha256": sha(MANIFEST_PATH),
        "producer_sha256": sha(PRODUCER),
        "common_sha256": sha(RUN.COMMON_PATH),
        "audit_source_sha256": sha(Path(__file__)),
        "ortools_version": ortools.__version__,
        "model_receipts": model_receipts,
        "fake_child_controls": children,
        "fake_runner_controls": runners,
        "positive_control": positive,
        "real_solver_launches": 0,
        "scope": (
            "Exact frozen three restricted models and bounded runner; "
            "no recipe feasibility or global theorem"
        ),
    }
    dump(HERE / "audit.json", result)
    print(
        json.dumps(
            {
                "passed": True,
                "model_damage_controls": 60,
                "child_cases": len(children),
                "runner_cases": len(runners),
                "real_solver_launches": 0,
                "audit_sha256": sha(HERE / "audit.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
