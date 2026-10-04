# Document:    Independent Soft Pair-Two Model Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import argparse
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
BASE = HERE.parent / "compact-pair-two-counts"
spec = importlib.util.spec_from_file_location(
    "hard_checker", HERE.parent / "pair-two-counts-independent/check.py"
)
hard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hard)
BLOCKS = list(combinations(range(1, 17), 5))
PAIRS = list(combinations(range(1, 17), 2))
TRIPLES = list(combinations(range(1, 17), 3))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main(source):
    source = source.resolve()
    manifest, parent = read(source / "manifest.json"), read(BASE / "manifest.json")
    assert sha(source / "prepare.py") == manifest["source_sha256"]
    for relative, digest in manifest["sources"].items():
        assert sha(ROOT / relative) == digest
    for relative, digest in manifest["frozen_proofs"].items():
        assert sha(HERE.parent / relative) == digest
    prior = read(HERE.parent / "pair-two-counts-independent/gate.json")
    assert prior["passed"] and prior["manifest_sha256"] == sha(BASE / "manifest.json")
    assert sha(ROOT / parent["model_path"]) == parent["model_sha256"] == prior["model_sha256"]
    assert sha(ROOT / manifest["model_path"]) == manifest["model_sha256"]
    model = text_format.Parse(
        (ROOT / manifest["model_path"]).read_text(), cp_model_pb2.CpModelProto()
    )
    old = text_format.Parse(
        (ROOT / parent["model_path"]).read_text(), cp_model_pb2.CpModelProto()
    )
    assert len(model.variables) == 5728 and len(model.constraints) == 14405
    assert all(list(v.domain) == [0, 128] for v in model.variables[5608:])
    normalized = copy.deepcopy(model)
    del normalized.variables[5608:]
    # Names are metadata; domains and every other field must remain identical.
    for variable, original_variable in zip(normalized.variables, old.variables, strict=True):
        variable.name = original_variable.name
    assert normalized.variables[:] == old.variables[:]
    del normalized.constraints[14404:]
    for row_index in range(3481, 14401):
        pair = (row_index - 3481) // 91
        target = model.constraints[row_index]
        assert list(target.linear.vars).count(5608 + pair) == 1
        stripped = copy.deepcopy(target)
        position = list(stripped.linear.vars).index(5608 + pair)
        assert stripped.linear.coeffs[position] == 1
        del stripped.linear.vars[position]
        del stripped.linear.coeffs[position]
        assert hard.row_key(stripped) == hard.row_key(old.constraints[row_index])
        normalized.constraints[row_index].CopyFrom(old.constraints[row_index])
    normalized.objective.CopyFrom(old.objective)
    normalized.solution_hint.CopyFrom(old.solution_hint)
    assert normalized == old
    core_proof = read(HERE.parent / "fourth-core-independent/audit.json")
    assert core_proof["passed"] and core_proof["recommended_upper_bound"] == 55
    fourth = core_proof["core_global_ids"]
    assert len(fourth) == len(set(fourth)) == 60
    assert hard.row_key(model.constraints[-1]) == hard.expected_key(
        dict.fromkeys(fourth, 1), -(2**63), 55
    )
    expected_objective = dict.fromkeys(range(5048, 5608), 1)
    expected_objective.update(dict.fromkeys(range(5608, 5728), 561))
    objective = dict(zip(model.objective.vars, model.objective.coeffs, strict=True))
    assert objective == expected_objective
    assert len(model.objective.vars) == 680
    assert model.objective.scaling_factor == 1 and model.objective.offset == 0
    candidate_path = ROOT / manifest["candidate_path"]
    assert sha(candidate_path) == manifest["candidate_sha256"]
    assert sha(candidate_path) == "a7feb783eb9f36e710feba5356857514cde146104b95de03fa47716126afd9c4"
    hint_path = ROOT / manifest["hint_path"]
    assert sha(hint_path) == manifest["hint_sha256"]
    blocks = [tuple(map(int, line.split())) for line in candidate_path.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) == 64 and all(b in BLOCKS for b in blocks)
    chosen = set(blocks)
    pc = Counter(p for b in blocks for p in combinations(b, 2))
    tc = Counter(t for b in blocks for t in combinations(b, 3))
    deficits = []
    for pair in PAIRS:
        counts = sorted((tc[tuple(sorted((*pair, a)))] for a in range(1, 17) if a not in pair),
                        reverse=True)
        deficits.append(max(0, 12 - 3 * pc[pair] + counts[0] + counts[1]))
    values = [int(b in chosen) for b in BLOCKS]
    values += [pc[p] for p in PAIRS] + [tc[t] for t in TRIPLES]
    values += [int(tc[t] == 0) for t in TRIPLES] + deficits
    hints = dict(zip(model.solution_hint.vars, model.solution_hint.values, strict=True))
    assert len(hints) == len(model.solution_hint.vars) == 5728
    assert values == [hints[i] for i in range(5728)]
    assert read(hint_path)["values"] == values
    assert not any(hard.failures(model, values).values())
    assert sum(deficits) == 74 and sum(values[5048:5608]) == 49
    assert sum(values[i] * c for i, c in expected_objective.items()) == 41563
    cores = parent["core_rows"] + [fourth]
    ids = {i for i, b in enumerate(BLOCKS) if b in chosen}
    assert [len(ids & set(core)) for core in cores] == [0, 2, 2, 4]
    index = next(i for i, value in enumerate(deficits) if value > 0)
    bad = values.copy()
    bad[5608 + index] -= 1
    assert hard.failures(model, bad)["constraint_indices"]
    slack = values.copy()
    slack[5608 + index] += 1
    assert not any(hard.failures(model, slack).values())
    parameters_path = ROOT / manifest["parameters_path"]
    assert sha(parameters_path) == manifest["parameters_sha256"]
    params = text_format.Parse(parameters_path.read_text(), sat_parameters_pb2.SatParameters())
    original = text_format.Parse(
        (ROOT / parent["parameters_path"]).read_text(), sat_parameters_pb2.SatParameters()
    )
    assert params.random_seed == 2026104302
    reverted = copy.deepcopy(params)
    reverted.random_seed = 2026104301
    assert reverted == original
    assert params.max_time_in_seconds == 120 and params.num_search_workers == 4
    runner = source / "execute.py"
    assert runner.exists()
    report = {
        "passed": True, "decision": "GO", "optimizer_calls": 0,
        "checker_sha256": sha(__file__),
        "source_directory": str(source.relative_to(ROOT)),
        "manifest_sha256": sha(source / "manifest.json"),
        "source_sha256": sha(source / "prepare.py"), "runner_source_sha256": sha(runner),
        "runner_sha256": sha(runner), "hint_sha256": sha(hint_path),
        "model_sha256": manifest["model_sha256"], "parameters_sha256": sha(parameters_path),
        "parent_gate_sha256": sha(HERE.parent / "pair-two-counts-independent/gate.json"),
        "fourth_core_audit_sha256": sha(HERE.parent / "fourth-core-independent/audit.json"),
        "variables": 5728, "rows": 14405, "soft_rows": 10920,
        "hint_holes": 49, "hint_actual_d2": 74, "hint_objective": 41563,
        "damaged_deficit_rejected": True, "slack_deficit_accepted": True,
        "scope": "Preparation gate only. Deficit auxiliaries may exceed actual maxima. "
        "The complete hint is feasible for this soft model, not the hard stronger model. "
        "All full covers remain eligible with zero deficits; no optimizer or covering claim.",
    }
    (HERE / "gate.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    main(parser.parse_args().source)
