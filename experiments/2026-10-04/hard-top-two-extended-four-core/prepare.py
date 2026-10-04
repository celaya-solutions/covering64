# Document:    Hard Top-Two Extended Four-Core Model Preparation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      ed0d7a0b49bcfcf4a3eba702daa139ba5533fcc3120fbcf6563acbd4a04c7354
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare only; no Solve or runner. H49 is infeasible block-only guidance."""

import hashlib
import importlib.util
import itertools
import json
import platform
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
RAW = ROOT / "experiments/scratch/hard-top-two-extended-four-core-20261004"
HELPER = DAY / "pair-top-two-readonly-plan-v2/derive_hint.py"
H49 = DAY / "native-pair-penalty/seed-2026104402/search-final-qualified.txt"
H49_SHA = "a7feb783eb9f36e710feba5356857514cde146104b95de03fa47716126afd9c4"
PROOF_BINDINGS = {
    "pair-two-topmax-proof/audit.json":
        "796bf612ebe939bad5d346c3ac4348ab77b072c12c987f35b5e09647fef64e22",
    "pair-two-topmax-proof/README.md":
        "db283441d2411d147456b55743fa1b88d6478dfc9de62af58928860b19cbf09e",
    "pair-two-topmax-proof/manifest.json":
        "117a3260f137fd45cded1757b1b20cab0541b647bcb896ed55329cebb959a2c2",
    "pair-top-two-readonly-plan-v2/README.md":
        "12525a5ef4f70d83e636e6f68e3aaacfd0e7838651a8198e13ef63afd8224f85",
    "pair-top-two-readonly-plan-v2/derive_hint.py":
        "8f920dee82c70b5ee53580d9514b9e900073b929c3dd79c30ffef397ddbbbba4",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main():
    require(not RAW.exists() and not (HERE / "manifest.json").exists(), "frozen output exists")
    require(sha(H49) == H49_SHA, "guidance hash mismatch")
    for relative, digest in PROOF_BINDINGS.items():
        require(sha(DAY / relative) == digest, f"proof source changed: {relative}")
    spec = importlib.util.spec_from_file_location("top_two_helper", HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    cores = helper.load_sources()
    sets = {size: tuple(itertools.combinations(range(1, 17), size)) for size in (2, 3, 5)}
    blocks = helper.parse(H49.read_text())
    block_ids = {block: index for index, block in enumerate(sets[5])}
    selected = {block_ids[block] for block in blocks}
    block_values = [int(index in selected) for index in range(4368)]
    counts = {size: Counter(subset for block in blocks
                            for subset in itertools.combinations(block, size)) for size in (2, 3)}
    diagnostic, rejected = helper.derive(H49)
    require(rejected is None and not diagnostic["qualified"], "H49 unexpectedly qualifies")
    require(diagnostic["holes"] == 49 and diagnostic["D2max"] == 74
            and diagnostic["D2sum"] == 170, "guidance recount mismatch")
    require(diagnostic["core_overlaps"] == [0, 2, 2, 4], "guidance core mismatch")
    verification = helper.dual_verify(blocks, 49)
    model = cp_model.CpModel()
    x = [model.new_bool_var(f"block_{index}") for index in range(4368)]
    count_vars = {}
    for size, lower in ((2, 5), (3, 0)):
        count_vars[size] = {subset: model.new_int_var(
            lower, 64, f"count_{size}_" + "_".join(map(str, subset))) for subset in sets[size]}
    holes = [model.new_bool_var("hole_" + "_".join(map(str, triple))) for triple in sets[3]]
    z_vars = {pair: model.new_int_var(0, 64, "z_" + "_".join(map(str, pair))) for pair in sets[2]}
    y_vars = {}
    for pair in sets[2]:
        for point in range(1, 17):
            if point not in pair:
                y_vars[pair, point] = model.new_int_var(
                    0, 64, "y_" + "_".join(map(str, (*pair, point))))
    model.add(sum(x) == 64)
    support = {size: {subset: [] for subset in sets[size]} for size in (2, 3)}
    for index, block in enumerate(sets[5]):
        for size in (2, 3):
            for subset in itertools.combinations(block, size):
                support[size][subset].append(index)
    for size in (2, 3):
        for subset in sets[size]:
            require(len(support[size][subset]) == (364 if size == 2 else 78), "count support")
            model.add(count_vars[size][subset] == sum(x[index] for index in support[size][subset]))
    for triple, hole in zip(sets[3], holes, strict=True):
        model.add(count_vars[3][triple] == 0).only_enforce_if(hole)
        model.add(count_vars[3][triple] >= 1).only_enforce_if(hole.Not())
    require(len(model.proto.constraints) == 1801, "base constraint count")
    canonical_failures = []
    for pair in sets[2]:
        outside = [point for point in range(1, 17) if point not in pair]
        for point in outside:
            triple = tuple(sorted((*pair, point)))
            model.add(y_vars[pair, point] >= count_vars[3][triple] - z_vars[pair])
        model.add(2 * z_vars[pair] + sum(y_vars[pair, point] for point in outside)
                  <= 3 * count_vars[2][pair] - 12)
        ordered = sorted([counts[3][tuple(sorted((*pair, point)))] for point in outside],
                         reverse=True)
        z = ordered[1]
        budget_deficit = max(0, 2 * z + sum(max(0, t - z) for t in ordered)
                             - 3 * counts[2][pair] + 12)
        if budget_deficit:
            canonical_failures.append({"pair": pair, "budget_deficit": budget_deficit})
    for core in cores:
        model.add(sum(x[index] for index in core) <= 55)
    model.minimize(sum(holes))
    for index, value in enumerate(block_values):
        model.add_hint(x[index], value)
    require(len(model.proto.variables) == 7408, "variable count")
    require(len(model.proto.constraints) == 3605, "constraint count")
    require(list(model.proto.solution_hint.vars) == list(range(4368)), "block-only hint indices")
    require(list(model.proto.solution_hint.values) == block_values, "block-only hint values")
    require(sum(block_values) == 64, "guidance cardinality")
    require(sum(row["budget_deficit"] for row in canonical_failures) == 74, "extension deficit")
    require(not model.validate(), "model validation failed")
    parameters = cp_model.CpSolver().parameters
    parameters.max_time_in_seconds = 120
    parameters.num_search_workers = 4
    parameters.random_seed = 2026104601
    parameters.log_search_progress = True
    parameters.log_to_stdout = False
    RAW.mkdir(parents=True)
    model_path, parameters_path = RAW / "model.pbtxt", RAW / "parameters.pbtxt"
    model_path.write_text(str(model.proto))
    parameters_path.write_text(str(parameters))
    guidance_path = RAW / "block-only-h49-guidance.json"
    diagnostic.pop("objective")
    dump(guidance_path, {
        "classification": "infeasible block-only guidance; no feasible auxiliary extension",
        "candidate_path": str(H49.relative_to(ROOT)), "candidate_sha256": H49_SHA,
        "variable_indices": list(range(4368)), "values": block_values,
        "hinted_variables": 4368, "unhinted_variables": 3040,
        "diagnostics": diagnostic, "canonical_failed_budgets": canonical_failures,
        "verification": verification, "feasible_warm_start": False})
    snapshot = RAW / "frozen-sources"
    snapshot.mkdir()
    sources = {}
    for source in (Path(__file__), HELPER, ROOT / "src/covering64/core.py",
                   ROOT / "scripts/check_cover.py"):
        shutil.copy2(source, snapshot / source.name)
        sources[str(source.relative_to(ROOT))] = sha(source)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    manifest = {
        "status": "PREPARED ONLY; independent serialized-model gate required; no Solve",
        "optimizer_calls": 0, "runner_prepared": False, "source_revision": revision,
        "source_sha256": sha(__file__), "sources": sources,
        "python_version": platform.python_version(), "ortools_version": ortools.__version__,
        "raw_directory": str(RAW.relative_to(ROOT)),
        "model_path": str(model_path.relative_to(ROOT)),
        "model_sha256": sha(model_path),
        "parameters_path": str(parameters_path.relative_to(ROOT)),
        "parameters_sha256": sha(parameters_path),
        "guidance_path": str(guidance_path.relative_to(ROOT)),
        "guidance_sha256": sha(guidance_path), "candidate_sha256": H49_SHA,
        "variables": 7408, "constraints": 3605, "objective": "holes only",
        "budget_seconds": 120, "workers": 4, "seed": 2026104601,
        "proof_bindings": PROOF_BINDINGS, "cover_preservation_receipts": helper.FROZEN,
        "core_rows": cores, "core_caps": [55] * 4,
        "variable_order": {"blocks": [0, 4367], "pairs": [4368, 4487],
                           "triples": [4488, 5047], "holes": [5048, 5607],
                           "z": [5608, 5727], "y": [5728, 7407]},
        "row_counts": {"cardinality": 1, "count_definitions": 680,
                       "hole_reifications": 1120, "hinges": 1680, "top_two_budgets": 120,
                       "core_caps": 4, "single_triple_cuts": 0, "explicit_two_triple_cuts": 0},
        "domains": {"blocks": [0, 1], "pairs": [5, 64], "triples": [0, 64],
                    "holes": [0, 1], "z": [0, 64], "y": [0, 64]},
        "guidance": {"type": "infeasible block-only", "entries": 4368, "ones": 64,
                     "unhinted_auxiliaries": 3040, "D2max": 74, "holes": 49,
                     "feasible_warm_start": False, "has_feasible_auxiliary_extension": False},
        "not_imposed": ["degree20", "regularity", "symmetry", "incumbent incidence",
                        "restricted block family", "global profile", "fixed blocks"],
        "projection_scope": "same integer/LP projection as explicit strong cuts with four caps",
        "unverified": "independent serialized-model audit and run gate are pending",
    }
    dump(HERE / "manifest.json", manifest)
    dump(HERE / "preparation.json", {
        "passed": True, "optimizer_calls": 0, "model_validation": "passed",
        "variables": 7408, "rows": 3605, "block_hint_entries": 4368,
        "canonical_budget_failures": len(canonical_failures), "D2max": 74,
        "no_feasible_H49_extension": True, "manifest_sha256": sha(HERE / "manifest.json")})
    print(json.dumps({"prepared": True, "optimizer_calls": 0, "variables": 7408,
                      "rows": 3605, "manifest_sha256": sha(HERE / "manifest.json")}))


if __name__ == "__main__":
    main()
