# Document:    Independent Pair-Minimum DP Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import importlib.util
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
ROOT = HERE.parents[2]
SOURCE = DAY / "global-five-heavy-pair-five"
BASE = DAY / "global-five-heavy-dp"
spec = importlib.util.spec_from_file_location(
    "base_gate", DAY / "global-five-heavy-dp-independent/check.py"
)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
sha, read = base.sha, base.read


def main():
    manifest = read(SOURCE / "manifest.json")
    assert sha(SOURCE / "prepare.py") == manifest["source_sha256"]
    for relative, digest in manifest["input_files"].items():
        assert sha(ROOT / relative) == digest
    parent = read(BASE / "manifest.json")
    parent_gate = read(DAY / "global-five-heavy-dp-independent/gate.json")
    assert parent_gate["passed"]
    assert parent_gate["manifest_sha256"] == sha(BASE / "manifest.json")
    assert parent_gate["model_sha256"] == parent["model_sha256"]
    assert manifest["parent_manifest_sha256"] == sha(BASE / "manifest.json")
    assert sha(ROOT / parent["model_path"]) == manifest["parent_model_sha256"]
    assert sha(ROOT / manifest["model_path"]) == manifest["model_sha256"]
    model = text_format.Parse(
        (ROOT / manifest["model_path"]).read_text(), cp_model_pb2.CpModelProto()
    )
    old = text_format.Parse(
        (ROOT / parent["model_path"]).read_text(), cp_model_pb2.CpModelProto()
    )
    assert len(model.variables) == 10488 and len(model.constraints) == 103465
    stripped = copy.deepcopy(model)
    del stripped.constraints[103345:]
    stripped.solution_hint.CopyFrom(old.solution_hint)
    assert stripped == old
    assert all(list(v.domain) == [0, 1] for v in model.variables[:4368])
    assert manifest["core_rows"] == parent["core_rows"]
    assert manifest["dag"] == parent["dag"]
    pairs = list(combinations(range(1, 17), 2))
    pair_rows = read(ROOT / manifest["pair_rows_path"])
    assert sha(ROOT / manifest["pair_rows_path"]) == manifest["pair_rows_sha256"]
    assert len(pair_rows) == 120
    for index, pair in enumerate(pairs):
        carriers = [i for i, block in enumerate(base.BLOCKS) if set(pair) <= set(block)]
        assert len(carriers) == 364
        row = model.constraints[103345 + index]
        base.check_row(row, dict.fromkeys(carriers, 1), 5, base.INT_MAX)
        assert pair_rows[index] == {
            "pair_id": index, "pair": list(pair), "row": 103345 + index,
            "block_ids": carriers, "lower_bound": 5,
        }
    hint_path = ROOT / manifest["hint_source_path"]
    assert sha(hint_path) == manifest["hint_sha256"]
    blocks = [tuple(map(int, line.split())) for line in hint_path.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) == 64 and all(b in base.BLOCKS for b in blocks)
    ids = sorted(base.BLOCKS.index(b) for b in blocks)
    hints = dict(zip(model.solution_hint.vars, model.solution_hint.values, strict=True))
    assert len(hints) == len(model.solution_hint.vars) == 10488
    values = [hints[i] for i in range(10488)]
    assert [i for i in range(4368) if values[i]] == ids == manifest["hint_ids"]
    assert sha(ROOT / manifest["hint_values_path"]) == manifest["hint_values_sha256"]
    assert values == read(ROOT / manifest["hint_values_path"])
    base.check_values(model, values)
    coverage = Counter(t for b in blocks for t in combinations(b, 3))
    pair_counts = Counter(p for b in blocks for p in combinations(b, 2))
    assert min(pair_counts[p] for p in pairs) == 5
    assert sum(coverage[t] == 0 for t in base.TRIPLES) == 6
    assert values[4368:4928] == [int(coverage[t] == 0) for t in base.TRIPLES]
    assert values[4958:6078] == [int(coverage[t] >= n) for t in base.TRIPLES for n in (6, 7)]
    states = read(ROOT / manifest["dag"]["states_path"])
    weights = [5 * (coverage[t] >= 6) + (coverage[t] >= 7) for t in base.TRIPLES]
    least = {0: 0}
    for state in states[1:]:
        least[state] = max(least[p] + weights[t] for p, t in base.transitions(state))
    assert values[6078:] == [least[s] for s in states]
    assert max(least[s] for s in states if s.bit_count() == 15) == 22
    overlaps = [len(set(ids) & set(core)) for core in manifest["core_rows"]]
    assert overlaps == [2, 2, 0]
    assert sum(values[i] * c for i, c in zip(
        model.objective.vars, model.objective.coeffs, strict=True
    )) == 392
    params_path = ROOT / manifest["parameters_path"]
    assert sha(params_path) == manifest["parameters_sha256"]
    params = text_format.Parse(params_path.read_text(), sat_parameters_pb2.SatParameters())
    previous_params = text_format.Parse(
        (ROOT / parent["parameters_path"]).read_text(), sat_parameters_pb2.SatParameters()
    )
    assert params.random_seed == 2026104105
    comparison = copy.deepcopy(params)
    comparison.random_seed = 2026104104
    assert comparison == previous_params
    assert params.max_time_in_seconds == 120 and params.num_search_workers == 4
    damaged = []
    row = model.constraints[103345]
    expected = dict(zip(row.linear.vars, row.linear.coeffs, strict=True))
    for name, mutate in (
        ("weak_pair_minimum", lambda r: r.linear.domain.__setitem__(0, 4)),
        ("missing_carrier", lambda r: r.linear.coeffs.__setitem__(0, 0)),
        ("conditional_pair", lambda r: r.enforcement_literal.append(0)),
    ):
        altered = copy.deepcopy(row)
        mutate(altered)
        try:
            base.check_row(altered, expected, 5, base.INT_MAX)
        except AssertionError:
            damaged.append(name)
        else:
            raise AssertionError("Damaged pair row accepted")
    runner = SOURCE / "execute.py"
    assert runner.exists()
    report = {
        "passed": True, "optimizer_calls": 0, "checker_sha256": sha(__file__),
        "manifest_sha256": sha(SOURCE / "manifest.json"),
        "source_sha256": sha(SOURCE / "prepare.py"),
        "runner_source_sha256": sha(runner), "model_sha256": manifest["model_sha256"],
        "parameters_sha256": sha(params_path), "variables": 10488, "rows": 103465,
        "parent_gate_sha256": sha(DAY / "global-five-heavy-dp-independent/gate.json"),
        "unchanged_prefix_rows": 103345, "pair_rows": 120, "pair_support_size": 364,
        "hint_holes": 6, "hint_objective": 392, "hint_minimum_pair_count": 5,
        "hint_maximum_partition_weight": 22, "hint_core_overlaps": overlaps,
        "damaged_rows_rejected": damaged,
        "pair_bound_proof": "A fixed pair is in fourteen required triples. Each block "
        "through it covers three, hence at least ceiling(14/3)=5 blocks are necessary.",
        "scope": "Only encoding and complete-hint validation; no solve or cover claim.",
    }
    (HERE / "gate.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
