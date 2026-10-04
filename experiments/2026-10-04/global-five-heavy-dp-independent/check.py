# Document:    Independent Global Five Heavy DP Model Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check serialized rows, domains, complete hints and independent reachability."""

import copy
import hashlib
import json
import struct
from collections import Counter
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
ROOT = HERE.parents[2]
SOURCE = DAY / "global-five-heavy-dp"
TRIPLES = list(combinations(range(1, 17), 3))
BLOCKS = list(combinations(range(1, 17), 5))
MASKS = [sum(1 << (p - 1) for p in t) for t in TRIPLES]
MASK_RANK = {mask: i for i, mask in enumerate(MASKS)}
INT_MIN, INT_MAX = -(2**63), 2**63 - 1


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def transitions(mask):
    points = [p for p in range(16) if mask >> p & 1]
    pivot = points[0]
    for a, b in combinations(points[1:], 2):
        triple = (1 << pivot) | (1 << a) | (1 << b)
        yield mask ^ triple, MASK_RANK[triple]


def dag():
    pending = [65535 ^ (1 << p) for p in range(16)]
    seen = set(pending)
    while pending:
        state = pending.pop()
        if not state:
            continue
        for parent, _ in transitions(state):
            if parent not in seen:
                seen.add(parent)
                pending.append(parent)
    states = sorted(seen, key=lambda s: (s.bit_count(), s))
    rank = {s: i for i, s in enumerate(states)}
    rows = [(rank[s], rank[p], t) for s in states if s for p, t in transitions(s)]
    return states, rows


def check_row(row, coefficients, lower, upper, literals=()):
    assert row.WhichOneof("constraint") == "linear"
    assert list(row.enforcement_literal) == list(literals)
    assert len(set(row.linear.vars)) == len(row.linear.vars)
    assert dict(zip(row.linear.vars, row.linear.coeffs, strict=True)) == coefficients
    assert list(row.linear.domain) == [lower, upper]


def check_values(model, values):
    assert len(values) == len(model.variables)
    for var, value in zip(model.variables, values, strict=True):
        assert any(var.domain[i] <= value <= var.domain[i + 1]
                   for i in range(0, len(var.domain), 2))
    for row in model.constraints:
        if not all(values[i] if i >= 0 else not values[-i - 1] for i in row.enforcement_literal):
            continue
        value = sum(values[i] * c for i, c in zip(row.linear.vars, row.linear.coeffs, strict=True))
        assert any(row.linear.domain[i] <= value <= row.linear.domain[i + 1]
                   for i in range(0, len(row.linear.domain), 2))


def main():
    manifest = read(SOURCE / "manifest.json")
    assert sha(SOURCE / "prepare.py") == manifest["source_sha256"]
    for path, digest in manifest["input_files"].items():
        assert sha(ROOT / path) == digest
    model_path = ROOT / manifest["model_path"]
    assert sha(model_path) == manifest["model_sha256"]
    model = text_format.Parse(model_path.read_text(), cp_model_pb2.CpModelProto())
    assert {field.name for field, _ in model.ListFields()} == {
        "variables", "constraints", "objective", "solution_hint"
    }
    assert len(model.variables) == 10488 and len(model.constraints) == 103345
    previous = read(DAY / "three-core-profile-release/manifest.json")
    prior_gate = read(DAY / "three-core-profile-release-independent/gate.json")
    assert prior_gate["passed"] and prior_gate["manifest_sha256"] == sha(
        DAY / "three-core-profile-release/manifest.json"
    )
    case = next(c for c in previous["cases"] if c["name"] == "full-4368")
    assert sha(ROOT / case["model_path"]) == case["model_sha256"]
    old = text_format.Parse((ROOT / case["model_path"]).read_text(), cp_model_pb2.CpModelProto())
    assert model.variables[:4958] == old.variables[:]
    assert model.constraints[:1188] == old.constraints[:]
    assert model.objective == old.objective
    assert manifest["core_rows"] == previous["core_rows"]
    assert manifest["retained_named_partitions"] == previous["partitions"]
    generated_states, generated_rows = dag()
    assert len(generated_states) == 4410 and len(generated_rows) == 99917
    states = read(ROOT / manifest["dag"]["states_path"])
    assert len(states) == len(set(states)) == 4410 and set(states) == set(generated_states)
    assert states[0] == 0
    assert [s.bit_count() for s in states] == sorted(s.bit_count() for s in states)
    positions = {s: i for i, s in enumerate(states)}
    rows = [(positions[generated_states[s]], positions[generated_states[p]], t)
            for s, p, t in generated_rows]
    saved_rows = list(struct.iter_unpack(
        "<III", (ROOT / manifest["dag"]["rows_path"]).read_bytes()
    ))
    assert Counter(rows) == Counter(saved_rows) and len(set(rows)) == 99917
    for label in ("states", "rows"):
        assert sha(ROOT / manifest["dag"][label + "_path"]) == manifest["dag"][label + "_sha256"]
    support = [[i for i, b in enumerate(BLOCKS) if set(t) <= set(b)] for t in TRIPLES]
    for t, carriers in enumerate(support):
        a, b = 4958 + 2 * t, 4959 + 2 * t
        for v, level in ((a, 6), (b, 7)):
            assert model.variables[v].name == f"global_triple_{t}_at_least_{level}"
            assert list(model.variables[v].domain) == [0, 1]
        coefficients = dict.fromkeys(carriers, 1)
        for offset, lower, upper, lit in (
            (0, 6, INT_MAX, a), (1, INT_MIN, 5, -a - 1),
            (2, 7, INT_MAX, b), (3, INT_MIN, 6, -b - 1),
        ):
            check_row(model.constraints[1188 + 4 * t + offset], coefficients, lower, upper, [lit])
    for i, state in enumerate(states):
        var = model.variables[6078 + i]
        assert var.name == f"dp_{state:04x}"
        assert list(var.domain) == [0, 26 if state.bit_count() == 15 else 2 * state.bit_count()]
    expected_rows = Counter((s, p, t) for s, p, t in rows)
    observed = Counter()
    for row in model.constraints[3428:]:
        assert row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
        assert len(row.linear.vars) == 4 and list(row.linear.domain) == [0, INT_MAX]
        entries = list(zip(row.linear.vars, row.linear.coeffs, strict=True))
        current = next(i - 6078 for i, c in entries if c == 1)
        parent = next(i - 6078 for i, c in entries if c == -1 and i >= 6078)
        t = next((i - 4958) // 2 for i, c in entries if c == -5)
        check_row(row, {6078 + current: 1, 6078 + parent: -1,
                        4958 + 2 * t: -5, 4959 + 2 * t: -1}, 0, INT_MAX)
        observed[(current, parent, t)] += 1
    assert observed == expected_rows
    hints = dict(zip(model.solution_hint.vars, model.solution_hint.values, strict=True))
    assert len(hints) == len(model.solution_hint.vars) == 10488
    values = [hints[i] for i in range(10488)]
    old_hints = dict(zip(old.solution_hint.vars, old.solution_hint.values, strict=True))
    assert values[:4958] == [old_hints[i] for i in range(4958)]
    counts = [sum(values[i] for i in carriers) for carriers in support]
    least = [0] * 4410
    for s, p, t in rows:
        least[s] = max(least[s], least[p] + 5 * (counts[t] >= 6) + (counts[t] >= 7))
    assert values[4958:6078] == [int(c >= level) for c in counts for level in (6, 7)]
    assert values[6078:] == least and max(least[i] for i, s in enumerate(states)
                                       if s.bit_count() == 15) == 24
    check_values(model, values)
    assert sum(count == 0 for count in counts) == 10
    params_path = ROOT / manifest["parameters_path"]
    assert sha(params_path) == manifest["parameters_sha256"]
    params = text_format.Parse(params_path.read_text(), sat_parameters_pb2.SatParameters())
    assert params.max_time_in_seconds == 120 and params.num_search_workers == 4
    assert params.random_seed == 2026104104 and params.log_search_progress
    assert not params.log_to_stdout
    controls = []
    row = model.constraints[3428]
    seven_index = next(i for i, (v, c) in enumerate(zip(
        row.linear.vars, row.linear.coeffs, strict=True
    )) if v < 6078 and c == -1)
    for label, change in (
        ("lost_seven_weight", lambda r: r.linear.coeffs.__setitem__(seven_index, 0)),
        ("relaxed_recurrence", lambda r: r.linear.domain.__setitem__(0, -1)),
        ("disabled_recurrence", lambda r: r.enforcement_literal.append(0)),
    ):
        damaged = copy.deepcopy(row)
        change(damaged)
        try:
            check_row(damaged, dict(zip(row.linear.vars, row.linear.coeffs, strict=True)),
                      0, INT_MAX)
        except AssertionError:
            controls.append(label)
        else:
            raise AssertionError("Damaged recurrence accepted")
    proof_path = HERE / "proof.json"
    proof = read(proof_path)
    assert proof["passed"]
    for path, expected in proof["sources"].items():
        assert sha(ROOT / path) == expected
    runner_path = SOURCE / "execute.py"
    assert runner_path.exists()
    report = {"passed": True, "optimizer_calls": 0, "checker_sha256": sha(__file__),
              "proof_sha256": sha(proof_path), "manifest_sha256": sha(SOURCE / "manifest.json"),
              "source_sha256": sha(SOURCE / "prepare.py"),
              "runner_source_sha256": sha(runner_path),
              "model_sha256": sha(model_path), "parameters_sha256": sha(params_path),
              "variables": 10488, "constraints": 103345, "unchanged_prefix_rows": 1188,
              "threshold_rows": 2240, "dp_states": 4410, "dp_rows": 99917,
              "hint_maximum_partition_weight": 24, "hint_holes": 10,
              "hint_objective": 651, "damaged_controls_rejected": controls,
              "scope": "Only encoding and complete-hint validation. "
                       "No optimization or covering claim."}
    (HERE / "gate.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
