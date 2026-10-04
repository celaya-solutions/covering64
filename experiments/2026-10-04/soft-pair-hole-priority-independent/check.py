# Document:    Independent Hole-Priority Soft Pair Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import ast
import copy
import hashlib
import importlib.util
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "soft-pair-hole-priority"
PRIOR = HERE.parent / "soft-pair-h12-start"
BLOCKS = list(combinations(range(1, 17), 5))
PAIRS = list(combinations(range(1, 17), 2))
TRIPLES = list(combinations(range(1, 17), 3))
spec = importlib.util.spec_from_file_location(
    "independent_rows", HERE.parent / "pair-two-counts-independent/check.py"
)
rows = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rows)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    manifest, old_manifest = read(SOURCE / "manifest.json"), read(PRIOR / "manifest.json")
    prior_gate_path = HERE.parent / "soft-pair-h12-independent/gate.json"
    prior_gate = read(prior_gate_path)
    assert sha(prior_gate_path) == manifest["prior_gate_sha256"]
    assert prior_gate["passed"] and prior_gate["decision"] == "GO"
    assert sha(PRIOR / "manifest.json") == prior_gate["manifest_sha256"]
    assert sha(PRIOR / "manifest.json") == manifest["prior_manifest_sha256"]
    assert sha(PRIOR / "execute.py") == prior_gate["runner_sha256"]
    assert sha(ROOT / old_manifest["parameters_path"]) == prior_gate["parameters_sha256"]
    assert sha(rows.__file__) == read(
        HERE.parent / "pair-two-counts-independent/gate.json"
    )["checker_sha256"]
    for relative, digest in (manifest["sources"] | manifest["input_files"]).items():
        assert sha(ROOT / relative) == digest
    for relative, digest in manifest["frozen_proofs"].items():
        assert sha(HERE.parent / relative) == digest
    for kind in ("model", "parameters", "hint"):
        assert sha(ROOT / manifest[f"{kind}_path"]) == manifest[f"{kind}_sha256"]
    assert sha(ROOT / old_manifest["model_path"]) == prior_gate["model_sha256"]
    model = text_format.Parse(
        (ROOT / manifest["model_path"]).read_text(), cp_model_pb2.CpModelProto()
    )
    old = text_format.Parse(
        (ROOT / old_manifest["model_path"]).read_text(), cp_model_pb2.CpModelProto()
    )
    normalized = copy.deepcopy(model)
    normalized.solution_hint.CopyFrom(old.solution_hint)
    normalized.objective.CopyFrom(old.objective)
    assert normalized == old
    assert len(model.variables) == 5728 and len(model.constraints) == 14405
    parameters = text_format.Parse(
        (ROOT / manifest["parameters_path"]).read_text(), sat_parameters_pb2.SatParameters()
    )
    old_parameters = text_format.Parse(
        (ROOT / old_manifest["parameters_path"]).read_text(), sat_parameters_pb2.SatParameters()
    )
    assert parameters.max_time_in_seconds == 300 and parameters.num_search_workers == 4
    assert parameters.random_seed == 2026105001
    reverted = copy.deepcopy(parameters)
    reverted.max_time_in_seconds = 300
    reverted.random_seed = 2026104901
    assert reverted == old_parameters
    candidate = ROOT / manifest["candidate_path"]
    assert sha(candidate) == manifest["candidate_sha256"]
    assert sha(candidate) == "cadb86e4f2243eada269dc314bca0bc5c238f5b0ca2bd9525dd0b67aad24c970"
    blocks = [tuple(map(int, line.split())) for line in candidate.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) == 64 and all(b in BLOCKS for b in blocks)
    chosen = set(blocks)
    pairs = Counter(p for b in blocks for p in combinations(b, 2))
    triples = Counter(t for b in blocks for t in combinations(b, 3))
    deficits = []
    full_deficit = 0
    for pair in PAIRS:
        counts = sorted(
            [triples[tuple(sorted((*pair, a)))] for a in range(1, 17) if a not in pair],
            reverse=True,
        )
        deficits.append(max(0, 12 - 3 * pairs[pair] + counts[0] + counts[1]))
        full_deficit += sum(max(0, 12 - 3 * pairs[pair] + a + b)
                            for a, b in combinations(counts, 2))
    values = [int(b in chosen) for b in BLOCKS]
    values += [pairs[p] for p in PAIRS] + [triples[t] for t in TRIPLES]
    values += [int(triples[t] == 0) for t in TRIPLES] + deficits
    assert list(model.solution_hint.vars) == list(range(5728))
    assert list(model.solution_hint.values) == read(ROOT / manifest["hint_path"])["values"]
    assert list(model.solution_hint.values) == values
    assert not any(rows.failures(model, values).values())
    assert sum(values[5048:5608]) == 12 and sum(deficits) == full_deficit == 32
    assert min(pairs.values()) == 5
    assert sum(values[i] * c for i, c in zip(model.objective.vars,
               model.objective.coeffs, strict=True)) == 184364
    ids = {i for i, b in enumerate(BLOCKS) if b in chosen}
    assert manifest["core_rows"] == old_manifest["core_rows"]
    assert [len(ids & set(core)) for core in manifest["core_rows"]] == [1, 1, 1, 2]
    index = next(i for i, d in enumerate(deficits) if d > 0)
    damaged = values.copy()
    damaged[5608 + index] -= 1
    assert rows.failures(model, damaged)["constraint_indices"]
    slack = values.copy()
    slack[5608 + index] += 1
    assert not any(rows.failures(model, slack).values())
    expected_objective = dict.fromkeys(range(5048, 5608), 15361)
    expected_objective.update(dict.fromkeys(range(5608, 5728), 1))
    assert len(model.objective.vars) == 680
    objective = dict(zip(model.objective.vars, model.objective.coeffs, strict=True))
    assert objective == expected_objective
    assert model.objective.scaling_factor == 1 and model.objective.offset == 0
    assert all(list(v.domain) == [0, 128] for v in model.variables[5608:])
    deficit_upper = sum(list(v.domain)[1] for v in model.variables[5608:])
    assert deficit_upper == 15360 and 15361 > deficit_upper
    runner_spec = importlib.util.spec_from_file_location("hole_runner", SOURCE / "execute.py")
    runner = importlib.util.module_from_spec(runner_spec)
    runner_spec.loader.exec_module(runner)
    metrics = {"holes": 12, "D2max": 0, "D2sum": 0, "D3": 0, "D4": 0,
               "minimum_pair_count": 5, "core_overlaps": [1, 1, 1, 2]}
    rejected = {name: {"valid": False} for name in ("package", "standalone")}
    valid = {name: {"valid": True} for name in ("package", "standalone")}
    profile = {"maximum": 0}
    assert runner.classify_record(metrics, rejected, profile) == (False, True)
    actual_start = metrics | {"D2max": 32, "D2sum": 32}
    assert runner.classify_record(actual_start, rejected, profile) == (False, False)
    synthetic_cover_metrics = metrics | {"holes": 0}
    assert runner.classify_record(synthetic_cover_metrics, valid, profile) == (True, False)
    disagreements_rejected = 0
    for labels, facts in [(valid, metrics), (rejected, synthetic_cover_metrics),
                          ({"package": {"valid": True}, "standalone": {"valid": False}},
                           synthetic_cover_metrics)]:
        try:
            runner.classify_record(facts, labels, profile)
        except ValueError:
            disagreements_rejected += 1
    assert disagreements_rejected == 3
    tree = ast.parse((SOURCE / "execute.py").read_text())
    stops = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == "stop_search"]
    solves = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Attribute) and n.func.attr == "solve"]
    assert len(stops) == len(solves) == 1
    assert any(isinstance(n, ast.If) and isinstance(n.test, ast.Name)
               and n.test.id == "covering" and stops[0] in list(ast.walk(n))
               for n in ast.walk(tree))
    report = {
        "passed": True, "decision": "GO", "optimizer_calls": 0,
        "checker_sha256": sha(__file__), "manifest_sha256": sha(SOURCE / "manifest.json"),
        "model_sha256": manifest["model_sha256"],
        "parameters_sha256": manifest["parameters_sha256"],
        "hint_sha256": manifest["hint_sha256"], "runner_sha256": sha(SOURCE / "execute.py"),
        "prior_gate_sha256": sha(prior_gate_path),
        "unchanged_model_except_hint_and_objective": True,
        "runner_diff_reviewed": True, "cover_only_stop_controls_passed": True,
        "classification_controls_are_synthetic_not_witnesses": True,
        "deficit_domain_upper_sum": 15360, "hole_coefficient": 15361,
        "hint_holes": 12, "hint_d2_max_sum": 32, "hint_d2_full_sum": 32,
        "hint_objective": 184364, "core_overlaps": [1, 1, 1, 2],
        "decreased_required_deficit_rejected": True, "auxiliary_slack_accepted": True,
        "budget_seconds": 300, "workers": 4, "seed": 2026105001,
        "scope": "One root-owned run of the frozen soft model. Stop only at a dual-verified cover. "
        "A zero actual deficit "
        "with positive holes is only a qualified partial hint. No covering or lower-bound claim.",
    }
    (HERE / "gate.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
