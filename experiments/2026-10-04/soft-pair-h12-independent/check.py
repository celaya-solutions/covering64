# Document:    Independent H12 Soft Pair Model Gate
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
SOURCE = HERE.parent / "soft-pair-h12-start"
PRIOR = HERE.parent / "soft-strong-pair-four-core"
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
    prior_gate_path = HERE.parent / "soft-pair-two-independent/gate.json"
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
    assert normalized == old
    assert len(model.variables) == 5728 and len(model.constraints) == 14405
    parameters = text_format.Parse(
        (ROOT / manifest["parameters_path"]).read_text(), sat_parameters_pb2.SatParameters()
    )
    old_parameters = text_format.Parse(
        (ROOT / old_manifest["parameters_path"]).read_text(), sat_parameters_pb2.SatParameters()
    )
    assert parameters.max_time_in_seconds == 300 and parameters.num_search_workers == 4
    assert parameters.random_seed == 2026104901
    reverted = copy.deepcopy(parameters)
    reverted.max_time_in_seconds = 120
    reverted.random_seed = 2026104302
    assert reverted == old_parameters
    candidate = ROOT / manifest["candidate_path"]
    assert sha(candidate) == manifest["candidate_sha256"]
    assert sha(candidate) == "330788e4a6f24e1852b047f5cd2447bfa83da66ea8c6daba3287eb53088c4b00"
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
    assert sum(values[5048:5608]) == 12 and sum(deficits) == full_deficit == 34
    assert min(pairs.values()) == 5
    assert sum(values[i] * c for i, c in zip(model.objective.vars,
               model.objective.coeffs, strict=True)) == 19086
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
    expected_runner = (PRIOR / "execute.py").read_text().replace(
        "soft-strong-pair-four-core-run-20261004", "soft-pair-h12-start-run-20261004"
    ).replace('manifest["sources"].items()',
              '(manifest["sources"] | manifest["input_files"]).items()')
    assert ast.dump(ast.parse(expected_runner)) == ast.dump(
        ast.parse((SOURCE / "execute.py").read_text())
    )
    report = {
        "passed": True, "decision": "GO", "optimizer_calls": 0,
        "checker_sha256": sha(__file__), "manifest_sha256": sha(SOURCE / "manifest.json"),
        "model_sha256": manifest["model_sha256"],
        "parameters_sha256": manifest["parameters_sha256"],
        "hint_sha256": manifest["hint_sha256"], "runner_sha256": sha(SOURCE / "execute.py"),
        "prior_gate_sha256": sha(prior_gate_path),
        "unchanged_model_except_hint": True,
        "runner_ast_identical_after_output_path_and_input_hash_extension": True,
        "hint_holes": 12, "hint_d2_max_sum": 34, "hint_d2_full_sum": 34,
        "hint_objective": 19086, "core_overlaps": [1, 1, 1, 2],
        "decreased_required_deficit_rejected": True, "auxiliary_slack_accepted": True,
        "budget_seconds": 300, "workers": 4, "seed": 2026104901,
        "scope": "One root-owned run of the frozen soft model. A zero actual deficit "
        "with positive holes is only a qualified partial hint. No covering or lower-bound claim.",
    }
    (HERE / "gate.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
