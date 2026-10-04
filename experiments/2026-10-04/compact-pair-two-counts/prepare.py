# Document:    Frozen Compact Full-Universe Pair-Two-Triple Count Model
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      27321b1066792d94c204e29f9b4db4995b07468e9c45b87360f23eb9e222631b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare a compact necessary-condition model; no optimization entry point."""

import hashlib
import itertools
import json
import resource
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import ortools
from ortools.sat import sat_parameters_pb2
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
RAW = ROOT / "experiments/scratch/compact-pair-two-counts-20261004"
BASE = DAY / "global-five-heavy-dp"
INVENTORY = DAY / "pair-five-hint-inventory"
PROOF = DAY / "pair-local-necessary-cuts-independent"
STRONG_PROOF = DAY / "pair-two-necessary-cuts-independent"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
SETS = {size: list(itertools.combinations(range(1, 17), size)) for size in (2, 3)}
STARTS = {2: 4368, 3: 4488}
HOLE_START = 5048


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def relative(path):
    return str(path.relative_to(ROOT))


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def full_value_diagnostic(model, values):
    assert len(values) == len(model.proto.variables) == 5608
    for variable, value in zip(model.proto.variables, values, strict=True):
        assert type(value) is int
        bounds = list(variable.domain)
        assert any(bounds[i] <= value <= bounds[i + 1] for i in range(0, len(bounds), 2))
    violations = []
    for row_id, row in enumerate(model.proto.constraints):
        assert row.has_linear()
        if not all(values[i] if i >= 0 else not values[-i - 1] for i in row.enforcement_literal):
            continue
        lhs = sum(
            values[i] * coefficient
            for i, coefficient in zip(row.linear.vars, row.linear.coeffs, strict=True)
        )
        bounds = list(row.linear.domain)
        if not any(bounds[i] <= lhs <= bounds[i + 1] for i in range(0, len(bounds), 2)):
            violations.append({"row_id": row_id, "lhs": lhs, "domain": bounds})
    return violations


def main():
    assert not RAW.exists() and not (HERE / "manifest.json").exists()
    previous = read(BASE / "manifest.json")
    core_audit_path = DAY / "core-cap-independent/audit.json"
    third_audit_path = DAY / "third-core-independent/audit.json"
    core_audit, third_audit = read(core_audit_path), read(third_audit_path)
    assert core_audit["passed"] and third_audit["passed"]
    assert core_audit["recommended_upper_bound"] == third_audit["recommended_upper_bound"] == 55
    cores = previous["core_rows"]
    assert len(cores) == 3 and all(len(core) == len(set(core)) == 60 for core in cores)
    assert cores[2] == third_audit["core_global_ids"]
    proof_path = PROOF / "audit.json"
    proof = read(proof_path)
    assert sha(proof_path) == "506205cd1e0f8334f0d690c6f4f9929cc08267422285b31935a76a424003e4a8"
    assert proof["passed"] and proof["optimizer_calls"] == 0
    assert proof["triple_cut_rows"] == 1680 and proof["quadruple_cut_rows"] == 10920
    assert proof["check_sha256"] == sha(PROOF / "check.py")
    proof_manifest = read(PROOF / "manifest.json")
    for name, checksum in proof_manifest["files"].items():
        assert sha(ROOT / name) == checksum
    strong_proof_path = STRONG_PROOF / "audit.json"
    assert sha(strong_proof_path) == (
        "db490b9d3cd3500eb2c85d36f803a73667ceed00e5251932608e7d1150e7099b"
    )
    strong_proof = read(strong_proof_path)
    assert strong_proof["passed"] and strong_proof["optimizer_calls"] == 0
    assert strong_proof["row_count"] == 10920
    assert strong_proof["checker_sha256"] == sha(STRONG_PROOF / "check.py")
    strong_manifest = read(STRONG_PROOF / "manifest.json")
    for name, checksum in strong_manifest["files"].items():
        assert sha(ROOT / name) == checksum
    inventory = read(INVENTORY / "result.json")
    assert inventory["passed"] and inventory["optimizer_calls"] == 0
    hint = inventory["best"]
    assert hint["sha256"] == "797dada195b23eecc808798eb12c8e4e7ccd7edd026fbdf22dea5b341f9ea2de"
    hint_path = ROOT / hint["path"]
    assert sha(hint_path) == hint["sha256"] and hint["holes"] == 6
    blocks = [tuple(map(int, line.split())) for line in hint_path.read_text().splitlines()]
    rank = {block: index for index, block in enumerate(BLOCKS)}
    assert len(blocks) == len(set(blocks)) == 64 and all(block in rank for block in blocks)
    ids = sorted(rank[block] for block in blocks)
    assert ids == hint["ids"]
    chosen = set(ids)
    counts = {
        size: Counter(subset for block in blocks for subset in itertools.combinations(block, size))
        for size in (2, 3)
    }
    support = {size: {subset: [] for subset in SETS[size]} for size in (2, 3)}
    for block_id, block in enumerate(BLOCKS):
        for size in (2, 3):
            for subset in itertools.combinations(block, size):
                support[size][subset].append(block_id)
    assert all(len(row) == 364 for row in support[2].values())
    assert all(len(row) == 78 for row in support[3].values())
    started = time.monotonic()
    model = cp_model.CpModel()
    x = [model.new_bool_var(f"block_{i}") for i in range(4368)]
    count_vars = {}
    for size in (2, 3):
        lower, upper = (5, 64) if size == 2 else (0, 64)
        count_vars[size] = {
            subset: model.new_int_var(lower, upper, f"count_{size}_{i}")
            for i, subset in enumerate(SETS[size])
        }
    holes = [model.new_bool_var(f"hole_{i}") for i in range(560)]
    assert len(model.proto.variables) == 5608
    model.add(sum(x) == 64)
    for size in (2, 3):
        for subset in SETS[size]:
            model.add(count_vars[size][subset] == sum(x[i] for i in support[size][subset]))
    assert len(model.proto.constraints) == 681
    for triple, hole in zip(SETS[3], holes, strict=True):
        model.add(count_vars[3][triple] == 0).only_enforce_if(hole)
        model.add(count_vars[3][triple] >= 1).only_enforce_if(hole.Not())
    assert len(model.proto.constraints) == 1801
    for triple in SETS[3]:
        for pair in itertools.combinations(triple, 2):
            model.add(3 * count_vars[2][pair] - count_vars[3][triple] >= 13)
    assert len(model.proto.constraints) == 3481
    for pair in SETS[2]:
        outside = [point for point in range(1, 17) if point not in pair]
        for a, b in itertools.combinations(outside, 2):
            first = tuple(sorted((*pair, a)))
            second = tuple(sorted((*pair, b)))
            model.add(3 * count_vars[2][pair] - count_vars[3][first] - count_vars[3][second] >= 12)
    assert len(model.proto.constraints) == 14401
    for core in cores:
        model.add(sum(x[i] for i in core) <= 55)
    model.minimize(65 * sum(holes) + sum(x[i] for i in cores[0]))
    for block_id, variable in enumerate(x):
        model.add_hint(variable, int(block_id in chosen))
    build_seconds = time.monotonic() - started
    assert len(model.proto.constraints) == 14404
    assert list(model.proto.solution_hint.vars) == list(range(4368))
    assert list(model.proto.solution_hint.values) == [int(i in chosen) for i in range(4368)]
    assert sum(model.proto.solution_hint.values) == 64
    assert not model.validate(), model.validate()
    values = [int(i in chosen) for i in range(4368)]
    for size in (2, 3):
        values.extend(counts[size][subset] for subset in SETS[size])
    values.extend(int(counts[3][triple] == 0) for triple in SETS[3])
    violations = full_value_diagnostic(model, values)
    assert len(violations) == 66
    assert sum(1801 <= row["row_id"] <= 3480 for row in violations) == 4
    assert sum(3481 <= row["row_id"] <= 14400 for row in violations) == 62
    seed_objective = 65 * sum(values[HOLE_START:]) + len(chosen & set(cores[0]))
    assert seed_objective == 392
    assert len(model.proto.variables) - len(model.proto.solution_hint.vars) == 1240
    parameters = sat_parameters_pb2.SatParameters(
        max_time_in_seconds=120,
        num_search_workers=4,
        random_seed=2026104301,
        log_search_progress=True,
        log_to_stdout=False,
    )
    RAW.mkdir()
    model_path, parameters_path = RAW / "full-4368-model.pbtxt", RAW / "parameters.pbtxt"
    model_path.write_text(str(model.proto))
    parameters_path.write_text(str(parameters))
    derived_path = RAW / "derived-infeasible-seed-values.json"
    dump(derived_path, values)
    frozen_hint = RAW / "guidance-six-holes.txt"
    shutil.copy2(hint_path, frozen_hint)
    dump(
        HERE / "guidance-diagnostic.json",
        {
            "path": hint["path"],
            "sha256": hint["sha256"],
            "holes": 6,
            "core_overlaps": hint["core_overlaps"],
            "minimum_pair_count": 5,
            "hypothetical_objective": seed_objective,
            "hinted_variables": 4368,
            "unhinted_auxiliaries": 1240,
            "complete_assignment_is_feasible": False,
            "violated_rows": violations,
            "violated_single_triple_rows": 4,
            "violated_two_triple_rows": 62,
            "derived_values_path": relative(derived_path),
            "derived_values_sha256": sha(derived_path),
            "scope": "All block variables only are hinted. The uniquely derived count/hole "
            "extension is infeasible. This is guidance; the solver may repair or reject it.",
        },
    )
    dump(
        HERE / "universe.json",
        {
            "labels": list(range(1, 17)),
            "blocks": BLOCKS,
            "pairs": SETS[2],
            "triples": SETS[3],
        },
    )
    proof_files = dict(proof_manifest["files"])
    proof_files.update(strong_manifest["files"])
    proof_files[relative(STRONG_PROOF / "manifest.json")] = sha(STRONG_PROOF / "manifest.json")
    proof_files.update(
        {
            relative(PROOF / "manifest.json"): sha(PROOF / "manifest.json"),
            relative(core_audit_path): sha(core_audit_path),
            relative(third_audit_path): sha(third_audit_path),
        }
    )
    proof_files.update(core_audit["sources"])
    proof_files.update(third_audit["sources"])
    for witness in proof["witness_checks"]:
        proof_files[witness["path"]] = witness["sha256"]
    for witness in strong_proof["witness_checks"]:
        proof_files[witness["path"]] = witness["sha256"]
    inputs = dict(previous["input_files"])
    inputs.update(proof_files)
    inputs.update(inventory["source_files"])
    inputs.update(inventory["audit_files"])
    for path in [Path(__file__), BASE / "manifest.json", INVENTORY / "result.json", hint_path]:
        inputs[relative(path)] = sha(path)
    for receipt in inventory["best_verifiers"]:
        inputs[receipt["path"]] = receipt["sha256"]
    for name, checksum in inputs.items():
        original = ROOT / name
        assert sha(original) == checksum
        target = RAW / "frozen-inputs" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, target)
        assert sha(target) == checksum
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    stats = {
        "variables": 5608,
        "rows": 14404,
        "build_seconds": build_seconds,
        "model_bytes": model_path.stat().st_size,
        "process_peak_rss_bytes": rss if sys.platform == "darwin" else 1024 * rss,
        "optimizer_calls": 0,
    }
    dump(HERE / "build-stats.json", stats)
    manifest = {
        "source_sha256": sha(__file__),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "ortools_version": ortools.__version__,
        "input_files": inputs,
        "proof_files": proof_files,
        "model_path": relative(model_path),
        "model_sha256": sha(model_path),
        "parameters_path": relative(parameters_path),
        "parameters_sha256": sha(parameters_path),
        "universe_path": relative(HERE / "universe.json"),
        "universe_sha256": sha(HERE / "universe.json"),
        "variables": 5608,
        "rows": 14404,
        "target_blocks": 64,
        "block_variable_ids": list(range(4368)),
        "block_labels_are_one_based": True,
        "block_ids_are_zero_based_lexicographic": True,
        "variable_ranges": {
            "blocks": [0, 4367],
            "pairs": [4368, 4487],
            "triples": [4488, 5047],
            "holes": [5048, 5607],
        },
        "row_ranges": {
            "cardinality": [0, 0],
            "count_definitions": [1, 680],
            "hole_channels": [681, 1800],
            "pair_triple_cuts": [1801, 3480],
            "pair_two_triple_cuts": [3481, 14400],
            "core_caps": [14401, 14403],
        },
        "count_domains": {"pairs": [5, 64], "triples": [0, 64]},
        "two_triple_cut_rows": 10920,
        "quadruple_count_variables_included": False,
        "supersedes_execution_of": "experiments/2026-10-04/compact-pair-local-counts",
        "superseded_manifest_sha256": sha(DAY / "compact-pair-local-counts/manifest.json"),
        "core_rows": cores,
        "core_upper_bound": 55,
        "objective": "65*holes + original_core_overlap",
        "hint_source_path": hint["path"],
        "hint_sha256": hint["sha256"],
        "hint_ids": ids,
        "hint_kind": "block-only infeasible guidance",
        "hinted_variable_count": 4368,
        "hint_is_complete": False,
        "hint_has_feasible_extension": False,
        "guidance_diagnostic_sha256": sha(HERE / "guidance-diagnostic.json"),
        "global_dp_included": False,
        "named_partition_filters_included": False,
        "degree_or_symmetry_restrictions": False,
        "budget": {"cases": 1, "seconds": 120, "workers": 4, "seed": 2026104301},
        "build_stats_sha256": sha(HERE / "build-stats.json"),
        "optimization_calls": 0,
        "scope": "Preparation only. All 4368 block variables remain free. All valid "
        "64-block covers extend uniquely to exact counts and zero hole flags, satisfy the "
        "audited local cuts and core caps, and remain in this model. Global profile checks "
        "are omitted from the model and must be applied to any future saved outputs. "
        "No independent gate or optimization result is claimed.",
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "source_sha256": sha(__file__),
                "model_sha256": sha(model_path),
                "parameters_sha256": sha(parameters_path),
                **stats,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
