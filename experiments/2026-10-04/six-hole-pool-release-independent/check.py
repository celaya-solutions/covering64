# Document:    Independent Six-Hole Release Preparation Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      74a692709a18f12a04fff4c576e95ab6a5aafd4c7097f6a5a02c0e9a71e7cf04
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Reconstruct both frozen models without importing the producer or optimizing."""

import ast
import importlib.util
import itertools
import json
import subprocess
from collections import Counter
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
ROOT = HERE.parents[2]
SOURCE = DAY / "six-hole-pool-release"
SOURCE_SHA = "68d5f0ffc21d3f69ed6d99d6004d3b23ec2ef1213b977220173eaaea4d4d0f04"
MANIFEST_SHA = "84eac4c5110c0f98c7f8e0b01b3cc29dcc1f51003fdad9aa1b8e502813e2be8c"
spec = importlib.util.spec_from_file_location(
    "release_independent_profile", DAY / "heterogeneous-profile-pool-independent/check.py"
)
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
basis = previous.basis
read, digest, dump = previous.read, basis.digest, basis.dump


def expected(pool, hint, cores, partitions):
    model = previous.expected(pool, hint, cores, partitions)
    objective = model.proto.objective
    objective.vars.clear()
    objective.coeffs.clear()
    objective.vars.extend(cores[0] + list(range(4368, 4928)))
    objective.coeffs.extend([1] * 60 + [65] * 560)
    return model


def check_values(model, values):
    assert len(values) == 4948 and all(value in (0, 1) for value in values)
    for row in model.proto.constraints:
        active = all(
            values[lit] if lit >= 0 else not values[-lit - 1] for lit in row.enforcement_literal
        )
        if active:
            value = sum(
                values[v] * c for v, c in zip(row.linear.vars, row.linear.coeffs, strict=True)
            )
            assert row.linear.domain[0] <= value <= row.linear.domain[1]
    return sum(
        values[v] * c
        for v, c in zip(model.proto.objective.vars, model.proto.objective.coeffs, strict=True)
    )


def assignment(ids, partitions):
    chosen = set(ids)
    assert len(ids) == len(chosen) == 64 and all(0 <= i < 4368 for i in ids)
    missing = set(basis.profile(ids)["holes"])
    return (
        [int(i in chosen) for i in range(4368)]
        + [int(i in missing) for i in range(560)]
        + [
            int(len(chosen & set(basis.SUPPORT[basis.TRIPLES.index(tuple(triple))])) >= threshold)
            for partition in partitions
            for triple in partition
            for threshold in (6, 7)
        ]
    )


def scan(ids):
    counts = Counter(t for i in ids for t in itertools.combinations(basis.BLOCKS[i], 3))
    heavy = [t for t in basis.TRIPLES if counts[t] >= 6]
    obstructions = []
    for five in itertools.combinations(heavy, 5):
        if (
            len(set(itertools.chain.from_iterable(five))) == 15
            and sum(counts[t] >= 7 for t in five) >= 2
        ):
            obstructions.append(
                {"triples": [list(t) for t in five], "counts": [counts[t] for t in five]}
            )
    return {
        "heavy_triples": [{"triple": list(t), "count": counts[t]} for t in heavy],
        "five_heavy_obstructions": obstructions,
    }


def verify(path, ids):
    expected_holes = [list(basis.TRIPLES[i]) for i in basis.profile(ids)["holes"]]
    reports = []
    for command in (
        ["uv", "run", "covering64", "verify", str(path), "--expected-blocks", "64"],
        ["uv", "run", "python", "scripts/check_cover.py", str(path), "--expected-blocks", "64"],
    ):
        response = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        result = json.loads(response.stdout)
        assert response.returncode == int(bool(expected_holes))
        assert result["blocks"] == 64 and result["uncovered"] == expected_holes
        assert result["valid"] == (not expected_holes)
        reports.append(result)
    assert reports[0]["canonical_sha256"] == reports[1]["canonical_sha256"]
    return reports


def check_model(model, pool, hint, cores, partitions):
    assert not model.validate(), model.validate()
    assert str(model.proto) == str(expected(pool, hint, cores, partitions).proto)
    assert len(model.proto.variables) == 4948 and len(model.proto.constraints) == 1166
    assert list(model.proto.solution_hint.vars) == list(range(4948))
    values = list(model.proto.solution_hint.values)
    assert values == assignment(hint, partitions)
    assert check_values(model, values) == 449
    assert sum(values[4368:4928]) == 6


def main():
    assert not (HERE / "gate.json").exists()
    manifest = read(SOURCE / "manifest.json")
    assert digest(SOURCE / "manifest.json") == MANIFEST_SHA
    assert digest(SOURCE / "run.py") == manifest["source_sha256"] == SOURCE_SHA
    assert manifest["ortools_version"] == ortools.__version__
    assert len(manifest["source_revision"]) == 40
    subprocess.run(["git", "cat-file", "-e", manifest["source_revision"]], cwd=ROOT, check=True)
    for mapping in (manifest["input_files"], manifest["proof_files"]):
        for path, checksum in mapping.items():
            assert digest(ROOT / path) == checksum
    prior_manifest = read(DAY / "heterogeneous-profile-pool/manifest.json")
    prior_gate = read(DAY / "heterogeneous-profile-pool-independent/gate.json")
    prior_post = read(DAY / "heterogeneous-profile-postcheck/audit.json")
    assert prior_gate["passed"] and prior_post["passed"]
    assert prior_gate["manifest_sha256"] == digest(DAY / "heterogeneous-profile-pool/manifest.json")
    assert prior_post["producer_manifest_sha256"] == digest(
        DAY / "heterogeneous-profile-pool/manifest.json"
    )
    assert prior_post["producer_result_sha256"] == digest(
        DAY / "heterogeneous-profile-pool/result.json"
    )
    raw_core = ROOT / "experiments/2026-10-03/partial-core-holes/core.txt"
    blocks = [tuple(map(int, line.split())) for line in raw_core.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) == 60 and all(b in basis.RANK for b in blocks)
    cores = [
        sorted(basis.RANK[tuple(sorted(mapping[p - 1] for p in block))] for block in blocks)
        for mapping in previous.core.MAPS
    ]
    assert manifest["core_rows"] == prior_manifest["core_rows"] == cores
    original = [[1, 3, 6], [2, 14, 15], [4, 8, 10], [5, 13, 16], [9, 11, 12]]
    partitions = [
        original,
        [sorted(previous.core.MAPS[1][p - 1] for p in triple) for triple in original],
    ]
    assert manifest["partitions"] == prior_manifest["partitions"] == partitions
    assert manifest["profile_rule"] == {
        "six_coefficient": 5,
        "seven_coefficient": 1,
        "upper_bound": 26,
    }
    assert manifest["threshold_indicators"] == prior_manifest["threshold_indicators"]
    table_path = DAY / "heterogeneous-profile-pool/threshold-truth-table.json"
    assert digest(table_path) == manifest["profile_threshold_truth_table_sha256"]
    tables = previous.truth_tables(read(table_path), zip(("original", "mapped"), partitions))
    records = [item for item in prior_post["checked_states"] if item["facts"]["holes"] == 6]
    assert len(records) == len(manifest["sources"]) == 4
    source_reports, missing = [], set()
    for record, saved in zip(records, manifest["sources"], strict=True):
        path = ROOT / record["path"]
        ids = basis.parse_seed(path)
        profile = basis.profile(ids)
        assert digest(path) == record["sha256"] == saved["sha256"]
        assert saved["path"] == record["path"] and saved["ids"] == ids
        assert saved["profile"] == profile and len(profile["holes"]) == 6
        assert saved["is_final_response"] == record["is_final_response"]
        found = scan(ids)
        assert not found["five_heavy_obstructions"]
        missing.update(profile["holes"])
        source_reports.append(
            {
                "path": record["path"],
                "sha256": digest(path),
                "profile": profile,
                "scan": found,
                "verifiers": verify(path, ids),
            }
        )
    elite = set().union(
        *(
            set(basis.parse_seed(ROOT / row["path"]))
            for row in read(DAY / "heterogeneous-seed-inventory/inventory.json")["entries"]
        )
    )
    assert (
        sorted(elite) == manifest["original_elite_global_ids"] == prior_manifest["cases"][0]["pool"]
    )
    assert len(elite) == 277 and len(missing) == 12
    carriers = set().union(*(set(basis.SUPPORT[t]) for t in missing))
    assert len(carriers) == 720
    assert sorted(missing) == manifest["hole_triple_ids"]
    assert [list(basis.TRIPLES[t]) for t in sorted(missing)] == manifest["hole_triples"]
    assert sorted(carriers) == manifest["hole_carrier_global_ids"]
    pools = [sorted(elite | carriers), list(range(4368))]
    assert len(pools[0]) == 952
    hint = basis.parse_seed(ROOT / manifest["hint_source_path"])
    assert hint == manifest["hint"] and set(hint) <= set(pools[0])
    assert digest(ROOT / manifest["hint_source_path"]) == manifest["hint_sha256"]
    assert manifest["hint_source_path"].endswith(
        "heterogeneous-profile-postcheck/elite-final-response.txt"
    )
    assert manifest["hint_holes"] == 6 and manifest["hint_original_core_overlap"] == 59
    assert manifest["hint_composite_objective"] == 449
    assert manifest["objective"] == {
        "hole_coefficient": 65,
        "original_core_coefficient": 1,
        "original_core_global_ids": cores[0],
        "rationale": "Core overlap is between 0 and 60; one fewer hole always wins.",
    }
    # All feasible overlaps are in [0,60]; even the largest tie shift is less than 65.
    assert all(65 + a > b for a in range(61) for b in range(61))
    assert manifest["budget"] == {"cases": 2, "seconds_per_case": 120, "workers": 4}
    assert manifest["seed"] == 2026104101 and manifest["optimization_calls"] == 0
    params = cp_model.CpSolver().parameters
    params.max_time_in_seconds = 120
    params.num_search_workers = 4
    params.random_seed = 2026104101
    params.log_search_progress = True
    params.log_to_stdout = False
    models, reports = [], []
    for case, pool, name in zip(
        manifest["cases"], pools, ("adaptive-952", "full-4368"), strict=True
    ):
        assert case["name"] == name and case["pool"] == pool and case["pool_size"] == len(pool)
        assert digest(ROOT / case["model_path"]) == case["model_sha256"]
        assert digest(ROOT / case["parameters_path"]) == case["parameters_sha256"]
        assert (ROOT / case["parameters_path"]).read_text() == str(params)
        model = cp_model.CpModel()
        model.proto.parse_text_format((ROOT / case["model_path"]).read_text())
        check_model(model, pool, hint, cores, partitions)
        models.append(model)
        reports.append(
            {
                "name": name,
                "pool_size": len(pool),
                "model_sha256": case["model_sha256"],
                "parameters_sha256": case["parameters_sha256"],
                "variables": 4948,
                "rows": 1166,
            }
        )
    assert len(models[1].proto.constraints[1].linear.vars) == 0
    source = ast.parse((SOURCE / "run.py").read_text())
    calls = [
        node
        for node in ast.walk(source)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "solve"
    ]
    assert len(calls) == 1 and ast.unparse(calls[0]) == "solver.solve(model, callback)"
    factory = next(
        n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == "solver_for"
    )
    assignments = {
        ast.unparse(n.targets[0]): ast.unparse(n.value)
        for n in ast.walk(factory)
        if isinstance(n, ast.Assign)
    }
    assert assignments == {
        "solver": "cp_model.CpSolver()",
        "solver.parameters.max_time_in_seconds": "120",
        "solver.parameters.num_search_workers": "4",
        "solver.parameters.random_seed": "SEED",
        "solver.parameters.log_search_progress": "True",
        "solver.parameters.log_to_stdout": "False",
    }
    controls = []
    for label, mutate in (
        ("cardinality", lambda p: p.constraints[0].linear.domain.__setitem__(0, 63)),
        ("hidden_full_pool_restriction", lambda p: p.constraints[1].linear.vars.append(1)),
        ("core_upper_bound", lambda p: p.constraints[1122].linear.domain.__setitem__(1, 58)),
        ("one_sided_threshold", lambda p: p.constraints[1125].enforcement_literal.clear()),
        ("unconditional_seven_cap", lambda p: p.constraints[1144].linear.domain.__setitem__(1, 25)),
        ("wrong_hole_weight", lambda p: p.objective.coeffs.__setitem__(60, 64)),
        ("wrong_core_preference", lambda p: p.objective.coeffs.__setitem__(0, -1)),
        ("wrong_hint", lambda p: p.solution_hint.values.__setitem__(0, 1)),
        ("extra_radius_row", lambda p: p.constraints.add().linear.domain.extend([0, 1])),
    ):
        damaged = models[1].clone()
        mutate(damaged.proto)
        assert basis.reject(lambda: check_model(damaged, pools[1], hint, cores, partitions))
        controls.append(label)
    dependencies = [
        Path(__file__),
        Path(previous.__file__),
        Path(previous.core.__file__),
        Path(basis.__file__),
    ]
    gate = {
        "passed": True,
        "manifest_sha256": MANIFEST_SHA,
        "source_sha256": SOURCE_SHA,
        "checker_sha256": digest(Path(__file__)),
        "optimizer_calls": 0,
        "cases": reports,
        "source_states": source_reports,
        "threshold_truth_tables": tables,
        "damaged_controls_rejected": controls,
        "independent_sources": {str(p.relative_to(ROOT)): digest(p) for p in dependencies},
        "pool_derivation": {
            "elite": 277,
            "source_states": 4,
            "distinct_holes": 12,
            "carriers": 720,
            "union": 952,
        },
        "scope": (
            "Preparation gate only; all slots released. Objective tie preference only. "
            "No optimization or global theorem."
        ),
    }
    dump(HERE / "gate.json", gate)
    print(
        json.dumps(
            {"passed": True, "gate_sha256": digest(HERE / "gate.json"), "optimizer_calls": 0}
        )
    )


if __name__ == "__main__":
    main()
