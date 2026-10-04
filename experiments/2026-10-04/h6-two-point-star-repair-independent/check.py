# Document:    H6 Two Point Star Repair Independent Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      950166f51d4358fab0cd2ab04bd6afd9bcaf0c76b6781adfc250fd71e111abb0
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Audit frozen proto and mock process limits; never call a real solver or child."""

import ast
import contextlib
import hashlib
import importlib.util
import io
import itertools
import json
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "h6-two-point-star-repair"
RAW = ROOT / "experiments/scratch/h6-two-point-star-repair-20261004"
MANIFEST_SHA = "29014890a28ed880861ced497d635d8d0ec75b6b5e815cac2e068ac0c2dc60dc"
RUNNER_SHA = "b177c7986a8c35b03013f3bd8da18102151794a52d564c938033cf2a1e2943fd"
MODEL_SHA = "32f04e29da51daa7983f2f64b75b966fe5779eae0e830df1ef5af5d4434d0814"
PARAMS_SHA = "871be3961403e8ebdede9b54e4c3bc69038cdbd499799907f02661a4a0615db0"
INITIAL_SHA = "2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855"
OLD_SHA = "708b31333b659e864f9ee4ab37c7ae9909833b13f7c64a229b4f6fbc6b2abdc7"
BLOCKS = tuple(itertools.combinations(range(1, 17), 5))
TRIPLES = tuple(itertools.combinations(range(1, 17), 3))
PAIRS = tuple(itertools.combinations(range(1, 17), 2))
MAXINT = 2**63 - 1
MININT = -(2**63)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rejected(action):
    try:
        action()
    except (AssertionError, ValueError, KeyError):
        return True
    return False


def main():
    assert sha(PRODUCER / "manifest.json") == MANIFEST_SHA
    assert sha(PRODUCER / "run.py") == RUNNER_SHA
    assert sha(RAW / "model.pbtxt") == MODEL_SHA
    assert sha(RAW / "parameters.pbtxt") == PARAMS_SHA
    assert sha(HERE.parent / "two-point-star-repair-v2/run.py") == OLD_SHA
    assert sha(PRODUCER / "controls.json") == (
        "4e1194a2caaec061a2a6599332637d0def24b5955646928d233d4e26f157fce7"
    )
    manifest = json.loads((PRODUCER / "manifest.json").read_text())
    for group in ("dependencies", "prepared_files"):
        for path, digest in manifest[group].items():
            assert sha(ROOT / path) == digest
    assert manifest["source_sha256"] == RUNNER_SHA
    assert manifest["model_sha256"] == MODEL_SHA
    assert manifest["parameters_sha256"] == PARAMS_SHA
    assert {
        k: manifest[k] for k in ("seconds", "workers", "seed", "watchdog", "grace", "max_calls")
    } == {
        "seconds": 120,
        "workers": 4,
        "seed": 2026106001,
        "watchdog": 140,
        "grace": 5,
        "max_calls": 1,
    }
    assert manifest["pivot"] == [6, 10] and manifest["initial_hint_feasible"] is False
    initial_path = HERE.parent / "native-h9-h10-reuse-pilot/seed-2026105901/search-final-raw64.txt"
    assert sha(initial_path) == INITIAL_SHA
    family = tuple(tuple(map(int, row.split())) for row in initial_path.read_text().splitlines())
    assert len(family) == len(set(family)) == 64 and list(family) == sorted(family)
    chosen = {BLOCKS.index(block) for block in family}
    triple_counts = Counter(t for b in family for t in itertools.combinations(b, 3))
    vector = [int(i in chosen) for i in range(4368)] + [int(triple_counts[t] == 0) for t in TRIPLES]
    assert json.loads((RAW / "initial-vector.json").read_text())["values"] == vector
    model = cp_model.CpModel()
    assert model.proto.parse_text_format((RAW / "model.pbtxt").read_text())
    assert model.validate() == ""
    fixed = [i for i, b in enumerate(BLOCKS) if not {6, 10}.intersection(b)]
    free = sorted(set(range(4368)) - set(fixed))
    assert (len(fixed), len(set(fixed) & chosen), len(free), len(set(free) & chosen)) == (
        2002,
        30,
        2366,
        34,
    )
    expected_rows = [(list(range(4368)), [], [64, 64])]
    for j, triple in enumerate(TRIPLES):
        carrier = [i for i, b in enumerate(BLOCKS) if set(triple) <= set(b)]
        assert len(carrier) == 78
        expected_rows.extend([(carrier, [4368 + j], [0, 0]), (carrier, [-4369 - j], [1, MAXINT])])
    for pair in PAIRS:
        carrier = [i for i, b in enumerate(BLOCKS) if set(pair) <= set(b)]
        assert len(carrier) == 364
        expected_rows.append((carrier, [], [5, MAXINT]))
    expected_rows.append((list(range(4368, 4928)), [], [MININT, 6]))
    assert len(expected_rows) == 1242

    def audit(proto):
        assert len(proto.variables) == 4928 and len(proto.constraints) == 1242
        assert proto.name == "" and not proto.assumptions and not proto.search_strategy
        assert not proto.has_floating_point_objective() and not proto.has_symmetry()
        for i, variable in enumerate(proto.variables):
            expected = type(variable)()
            expected.name = f"b_{i}" if i < 4368 else f"h_{i - 4368}"
            domain = [vector[i], vector[i]] if i in fixed else [0, 1]
            expected.domain.extend(domain)
            assert str(variable) == str(expected), ("variable", i)
        for i, (row, (variables, enforcement, domain)) in enumerate(
            zip(proto.constraints, expected_rows)
        ):
            expected = type(row)()
            expected.linear.vars.extend(variables)
            expected.linear.coeffs.extend([1] * len(variables))
            expected.linear.domain.extend(domain)
            expected.enforcement_literal.extend(enforcement)
            assert str(row) == str(expected), ("row", i)
        objective = type(proto.objective)()
        objective.vars.extend(range(4368, 4928))
        objective.coeffs.extend([1] * 560)
        objective.scaling_factor = 1
        assert proto.has_objective() and str(proto.objective) == str(objective)
        hint = type(proto.solution_hint)()
        hint.vars.extend([*range(4368, 4928), *range(4368)])
        hint.values.extend([*vector[4368:], *vector[:4368]])
        assert proto.has_solution_hint() and str(proto.solution_hint) == str(hint)

    audit(model.proto)
    errors = []
    for index, (variables, literals, domain) in enumerate(expected_rows):
        if all(vector[e] if e >= 0 else not vector[-e - 1] for e in literals):
            amount = sum(vector[i] for i in variables)
            if not domain[0] <= amount <= domain[1]:
                errors.append(
                    {
                        "kind": "linear",
                        "row": index,
                        "amount": amount,
                        "domain": domain,
                        "pair": list(PAIRS[index - 1121]),
                    }
                )
    assert [row["row"] for row in errors] == [1164, 1175, 1221]
    assert [row["pair"] for row in errors] == [[4, 6], [5, 6], [10, 12]]
    hint_audit = json.loads((PRODUCER / "initial-hint-audit.json").read_text())
    assert hint_audit["violations"] == errors
    assert hint_audit["feasible"] is False and hint_audit["complete"] is True
    assert hint_audit["blocks"] == 64 and hint_audit["hole_count"] == sum(vector[4368:]) == 6
    params = cp_model.CpSolver().parameters
    params.random_seed = 2026106001
    params.max_time_in_seconds = 120
    params.log_search_progress = True
    params.num_search_workers = 4
    incoming = type(params)()
    assert incoming.parse_text_format((RAW / "parameters.pbtxt").read_text())
    assert str(incoming) == str(params)
    assert incoming.fix_variables_to_their_hinted_value is False

    mutations = [
        ("wrong_fixed_domain", lambda p: p.variables[fixed[0]].domain.__setitem__(0, 1)),
        ("fixed_membership_released", lambda p: p.variables[fixed[0]].domain.__setitem__(1, 1)),
        ("free_membership_fixed", lambda p: p.variables[free[0]].domain.__setitem__(1, 0)),
        ("wrong_cardinality", lambda p: p.constraints[0].linear.domain.__setitem__(0, 63)),
        ("wrong_zero_flag", lambda p: p.constraints[1].enforcement_literal.__setitem__(0, 4369)),
        ("covered_allowed_zero", lambda p: p.constraints[2].linear.domain.__setitem__(0, 0)),
        ("damaged_triple_carrier", lambda p: p.constraints[1].linear.vars.__setitem__(0, 4367)),
        ("damaged_triple_coefficient", lambda p: p.constraints[1].linear.coeffs.__setitem__(0, 2)),
        ("weakened_pair_floor", lambda p: p.constraints[1164].linear.domain.__setitem__(0, 4)),
        ("weakened_hole_cap", lambda p: p.constraints[1241].linear.domain.__setitem__(1, 7)),
        ("wrong_objective_variable", lambda p: p.objective.vars.__setitem__(0, 0)),
        ("reversed_objective", lambda p: setattr(p.objective, "scaling_factor", -1)),
        ("hidden_assumption", lambda p: p.assumptions.append(0)),
        (
            "damaged_hint",
            lambda p: p.solution_hint.values.__setitem__(0, 1 - p.solution_hint.values[0]),
        ),
        ("duplicate_hint_variable", lambda p: p.solution_hint.vars.__setitem__(0, 4369)),
        ("nonlex_variable_name", lambda p: setattr(p.variables[0], "name", "wrong")),
    ]
    rejected_models = []
    for name, mutate in mutations:
        damaged = cp_model.CpModel()
        damaged.proto.copy_from(model.proto)
        mutate(damaged.proto)
        assert rejected(lambda: audit(damaged.proto)), name
        rejected_models.append(name)

    source = ast.parse((PRODUCER / "run.py").read_text())
    calls = [n for n in ast.walk(source) if isinstance(n, ast.Call)]
    assert sum(isinstance(n.func, ast.Attribute) and n.func.attr == "solve" for n in calls) == 1
    assert sum(isinstance(n.func, ast.Attribute) and n.func.attr == "Popen" for n in calls) == 1
    spec = importlib.util.spec_from_file_location("independent_gate_pilot", PRODUCER / "run.py")
    pilot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pilot)
    traces = []
    with tempfile.TemporaryDirectory(
        prefix="h6-star-independent-", dir=ROOT / "experiments/scratch"
    ) as temp:
        temp = Path(temp)
        gate_path = temp / "mock-gate.json"
        gate_path.write_text(
            json.dumps({"decision": "GO", "passed": True, "manifest_sha256": MANIFEST_SHA})
        )
        assert pilot.preflight(gate_path) == manifest
        assert rejected(lambda: pilot.check_vector(model, vector))
        for name, waits in [
            ("normal", [0]),
            ("terminate", [None, -15]),
            ("kill", [None, None, -9]),
        ]:
            events = []

            class FakeProcess:
                returncode = None

                def wait(self, timeout=None):
                    events.append(["wait", timeout])
                    result = waits.pop(0)
                    if result is None:
                        raise subprocess.TimeoutExpired("mock", timeout)
                    self.returncode = result

                def terminate(self):
                    events.append(["terminate"])

                def kill(self):
                    events.append(["kill"])

            root = temp / name
            raw = root / "raw"
            raw.mkdir(parents=True)
            (root / "manifest.json").write_bytes((PRODUCER / "manifest.json").read_bytes())
            with (
                patch.object(pilot, "HERE", root),
                patch.object(pilot, "RAW", raw),
                patch.object(pilot, "preflight", return_value=manifest),
                patch.object(pilot.subprocess, "Popen", return_value=FakeProcess()) as popen,
                patch.object(
                    pilot.cp_model.CpSolver, "solve", side_effect=AssertionError("no solve")
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                pilot.execute(gate_path)
                assert popen.call_count == 1
                assert rejected(lambda: pilot.execute(gate_path)) and popen.call_count == 1
            result = json.loads((root / "result.json").read_text())
            assert result["calls"] == 1 and result["relaunch"] is False
            assert result["saved"] == [] and result["cover_found"] is False
            assert result["watchdog_fired"] is (name != "normal")
            expected = {
                "normal": [["wait", 140]],
                "terminate": [["wait", 140], ["terminate"], ["wait", 5]],
                "kill": [["wait", 140], ["terminate"], ["wait", 5], ["kill"], ["wait", None]],
            }[name]
            assert events == expected
            traces.append(
                {"path": name, "events": events, "mock_processes": 1, "relaunch_rejected": True}
            )
    producer_controls = json.loads((PRODUCER / "controls.json").read_text())
    assert producer_controls["passed"] and len(producer_controls["controls"]) == 23
    assert all(v is True for v in producer_controls["controls"].values())
    assert producer_controls["real_optimization_calls"] == 0
    receipt = {
        "passed": True,
        "source_sha256": sha(Path(__file__)),
        "manifest_sha256": MANIFEST_SHA,
        "runner_sha256": RUNNER_SHA,
        "model_sha256": MODEL_SHA,
        "parameters_sha256": PARAMS_SHA,
        "initial_sha256": INITIAL_SHA,
        "variables_checked": 4928,
        "constraints_checked": 1242,
        "triple_flags_checked": 560,
        "pair_floor_rows_checked": 120,
        "fixed_memberships": 2002,
        "fixed_selected": 30,
        "free_memberships": 2366,
        "free_selected": 34,
        "initial_hint_feasible": False,
        "initial_hint_violations": errors,
        "damaged_models_rejected": rejected_models,
        "mock_process_paths": traces,
        "producer_controls_source_sha256": sha(PRODUCER / "controls.py"),
        "producer_controls_sha256": sha(PRODUCER / "controls.json"),
        "producer_controls_reviewed": 23,
        "optimizer_launches": 0,
        "native_process_launches": 0,
        "scope": (
            "One fixed {6,10} neighborhood; exact64 and H<=6 with pair floor5. "
            "No D2/D3/D4, named-core, degree, or rotational constraints. "
            "The initial hint is complete but infeasible. No global claim."
        ),
    }
    path = HERE / "checks.json"
    assert not path.exists()
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "checks_sha256": sha(path), "optimizer_launches": 0}))


if __name__ == "__main__":
    main()
