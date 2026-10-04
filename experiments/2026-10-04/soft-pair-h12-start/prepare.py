# Document:    Soft Strong-Pair H12 Hint Preparation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      137b4ab465904a01da9741b4bad2392706703edcfd0653b9e45d842b2553ff06
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare a complete feasible soft-pair hint and frozen model; never Solve."""

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
RAW = ROOT / "experiments/scratch/soft-pair-h12-start-20261004"
HELPER = HERE.parent / "pair-top-two-readonly-plan-v2/derive_hint.py"
HINT = HERE.parent / "native-variable-cardinality/seed-2026104702/search-final-admissible64.txt"
HINT_SHA = "330788e4a6f24e1852b047f5cd2447bfa83da66ea8c6daba3287eb53088c4b00"
SETS = {s: tuple(itertools.combinations(range(1, 17), s)) for s in (2, 3, 4, 5)}

PRIOR = HERE.parent / "soft-strong-pair-four-core"
INPUT_BINDINGS = {
    "soft-strong-pair-four-core/manifest.json": (
        "27f6839e030bd2ba7e940847282cc619e786151316d1b657ac471cef8e77b231"
    ),
    "soft-pair-two-independent/gate.json": (
        "6d613f6ea9fe047cd2c49e595637bca88dfa871233f44117083ab1fc09b1e203"
    ),
    "native-partial-start-profiles/manifest.json": (
        "0fe23f0125a8677d349c4d60aadfa49323d5a06edb411e6398a5c1600aa8d73c"
    ),
    "native-partial-start-profiles/diagnostic.json": (
        "90b8ddfbe4a5877ab1d45aec2052a1475c1028e65251e4fdd261e32e9c8cfd8c"
    ),
    "native-variable-cardinality-relabel-screen/manifest.json": (
        "50b83a48399e2f3f6458181987eeee94e4d847c1b5d13a31aa0f7a598d26870e"
    ),
    "native-variable-cardinality-relabel-screen/screen.json": (
        "159ca06adb57ed636e52d19da8d42c36a35d26a56827bfcd840f8c2b91bc3e98"
    ),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def helper_module():
    spec = importlib.util.spec_from_file_location("pure_top_two_helper", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def recount(ids, cores):
    require = helper_module().require
    require(len(ids) == len(set(ids)) == 64, "64 distinct IDs required")
    require(all(type(i) is int and 0 <= i < 4368 for i in ids), "invalid block ID")
    chosen = set(ids)
    blocks = [SETS[5][i] for i in sorted(ids)]
    counts = {
        s: Counter(q for block in blocks for q in itertools.combinations(block, s))
        for s in (2, 3, 4)
    }
    x = [int(i in chosen) for i in range(4368)]
    pairs = [counts[2][pair] for pair in SETS[2]]
    triples = [counts[3][triple] for triple in SETS[3]]
    holes = [int(value == 0) for value in triples]
    deficits, detail = [], []
    d3 = d4 = d2sum = 0
    for pair in SETS[2]:
        positions = [
            (a, counts[3][tuple(sorted((*pair, a)))]) for a in range(1, 17) if a not in pair
        ]
        r = counts[2][pair]
        require(sum(t for _, t in positions) == 3 * r, "incidence identity")
        ordered = sorted(positions, key=lambda item: (-item[1], item[0]))
        deficit = max(0, 12 - 3 * r + ordered[0][1] + ordered[1][1])
        deficits.append(deficit)
        local = [
            max(0, 12 - 3 * r + ta + tb)
            for (_, ta), (_, tb) in itertools.combinations(positions, 2)
        ]
        require(len(local) == 91 and max(local) == deficit, "D2max recount mismatch")
        d2sum += sum(local)
        d3 += sum(max(0, 13 - 3 * r + t) for _, t in positions)
        d4 += sum(
            max(0, 12 - 3 * r + 2 * counts[4][tuple(sorted((*pair, a, b)))])
            for (a, _), (b, _) in itertools.combinations(positions, 2)
        )
        detail.append(
            {"pair": pair, "positions": positions, "deficit": deficit, "D2sum": sum(local)}
        )
    overlap = [sum(x[i] for i in core) for core in cores]
    metrics = {
        "holes": sum(holes),
        "D2max": sum(deficits),
        "D2sum": d2sum,
        "D3": d3,
        "D4": d4,
        "minimum_pair_count": min(pairs),
        "core_overlaps": overlap,
        "canonical_objective": 561 * sum(deficits) + sum(holes),
    }
    return {
        "values": x + pairs + triples + holes + deficits,
        "metrics": metrics,
        "pair_details": detail,
        "blocks": blocks,
        "triple_counts": counts[3],
        "quadruple_counts": counts[4],
    }


def check_vector(model, values):
    require = helper_module().require
    require(len(values) == len(model.proto.variables), "incomplete vector")
    for index, (var, value) in enumerate(zip(model.proto.variables, values, strict=True)):
        domain = list(var.domain)
        require(
            type(value) is int
            and any(domain[i] <= value <= domain[i + 1] for i in range(0, len(domain), 2)),
            f"variable domain violation {index}",
        )
    enforced = 0
    for index, constraint in enumerate(model.proto.constraints):
        literals = list(constraint.enforcement_literal)
        active = all(values[lit] == 1 if lit >= 0 else values[-lit - 1] == 0 for lit in literals)
        require(constraint.has_linear(), f"nonlinear constraint {index}")
        if not active:
            continue
        enforced += 1
        linear = constraint.linear
        value = sum(
            coefficient * values[var]
            for var, coefficient in zip(linear.vars, linear.coeffs, strict=True)
        )
        domain = list(linear.domain)
        require(
            any(domain[i] <= value <= domain[i + 1] for i in range(0, len(domain), 2)),
            f"linear row violation {index}",
        )
    objective = model.proto.objective
    actual = objective.scaling_factor * (
        objective.offset
        + sum(
            coefficient * values[var]
            for var, coefficient in zip(objective.vars, objective.coeffs, strict=True)
        )
    )
    return {
        "variables_checked": len(values),
        "rows_checked": len(model.proto.constraints),
        "enforced_rows_checked": enforced,
        "objective": actual,
    }


def bound_inputs():
    require = helper_module().require
    files = {
        str((HERE.parent / path).relative_to(ROOT)): digest
        for path, digest in INPUT_BINDINGS.items()
    }
    prior = json.loads((PRIOR / "manifest.json").read_text())
    gate = json.loads((HERE.parent / "soft-pair-two-independent/gate.json").read_text())
    require(gate.get("passed") is True and gate.get("decision") == "GO", "prior gate not GO")
    require(gate["manifest_sha256"] == sha(PRIOR / "manifest.json"), "prior gate manifest")
    for kind in ("model", "parameters", "hint"):
        require(gate[f"{kind}_sha256"] == prior[f"{kind}_sha256"], "prior gate binding")
        files[prior[f"{kind}_path"]] = prior[f"{kind}_sha256"]
    files.update(prior["sources"])
    for directory in (
        "native-partial-start-profiles",
        "native-variable-cardinality-relabel-screen",
    ):
        manifest = json.loads((HERE.parent / directory / "manifest.json").read_text())
        files.update(manifest["files"])
    files[str(HINT.relative_to(ROOT))] = HINT_SHA
    for relative, digest in files.items():
        require(sha(ROOT / relative) == digest, f"bound input changed: {relative}")
    diagnostic = json.loads(
        (HERE.parent / "native-partial-start-profiles/diagnostic.json").read_text()
    )
    return files, prior, gate, diagnostic["profiles"]["H12"]


def direct_hint(blocks):
    """Derive the complete vector independently by direct set containment."""
    chosen = set(blocks)
    block_sets = [set(block) for block in blocks]
    counts = {
        size: {q: sum(set(q) <= block for block in block_sets) for q in SETS[size]}
        for size in (2, 3)
    }
    pairs = [counts[2][q] for q in SETS[2]]
    triples = [counts[3][q] for q in SETS[3]]
    deficits = [
        max(
            max(
                0,
                12
                - 3 * counts[2][pair]
                + counts[3][tuple(sorted((*pair, a)))]
                + counts[3][tuple(sorted((*pair, b)))],
            )
            for a, b in itertools.combinations([x for x in range(1, 17) if x not in pair], 2)
        )
        for pair in SETS[2]
    ]
    return (
        [int(block in chosen) for block in SETS[5]]
        + pairs
        + triples
        + [int(count == 0) for count in triples]
        + deficits
    )


def main():
    require = helper_module().require
    require(not RAW.exists() and not (HERE / "manifest.json").exists(), "existing frozen output")
    require(sha(HINT) == HINT_SHA, "H12 hash mismatch")
    helper = helper_module()
    input_files, prior, prior_gate, diagnostic = bound_inputs()
    cores = helper.load_sources()
    require(cores == prior["core_rows"], "prior core rows changed")
    blocks = helper.parse(HINT.read_text())
    lookup = {block: i for i, block in enumerate(SETS[5])}
    ids = sorted(lookup[block] for block in blocks)
    initial = recount(ids, cores)
    metrics = initial["metrics"]
    require(initial["values"] == direct_hint(blocks), "independent complete hint mismatch")
    require(
        diagnostic["sha256"] == HINT_SHA and diagnostic["holes"] == metrics["holes"],
        "profile candidate mismatch",
    )
    require(diagnostic["four_named_core_overlaps"] == metrics["core_overlaps"], "profile cores")
    for label, category, statistic in (
        ("D3", "single", "full_row_sum"),
        ("D4", "quad", "full_row_sum"),
        ("D2max", "two_triple", "sum_of_per_pair_maxima"),
        ("D2sum", "two_triple", "full_row_sum"),
    ):
        require(metrics[label] == diagnostic["deficits"][category][statistic], "profile deficits")
    require(
        metrics
        == {
            "holes": 12,
            "D2max": 34,
            "D2sum": 34,
            "D3": 0,
            "D4": 0,
            "minimum_pair_count": 5,
            "core_overlaps": [1, 1, 1, 2],
            "canonical_objective": 19086,
        },
        "unexpected H12 recount",
    )
    verification = helper.dual_verify(blocks, 12)
    profile = helper.global_profile(initial["triple_counts"])
    model = cp_model.CpModel()
    x = [model.new_bool_var(f"block_{i}") for i in range(4368)]
    count_vars = {}
    for size, lower in ((2, 5), (3, 0)):
        count_vars[size] = {
            q: model.new_int_var(lower, 64, f"count_{size}_" + "_".join(map(str, q)))
            for q in SETS[size]
        }
    hole_vars = [model.new_bool_var("hole_" + "_".join(map(str, q))) for q in SETS[3]]
    d_vars = {q: model.new_int_var(0, 128, "deficit_" + "_".join(map(str, q))) for q in SETS[2]}
    model.add(sum(x) == 64)
    support = {size: {q: [] for q in SETS[size]} for size in (2, 3)}
    for index, block in enumerate(SETS[5]):
        for size in (2, 3):
            for q in itertools.combinations(block, size):
                support[size][q].append(index)
    for size in (2, 3):
        for q in SETS[size]:
            require(len(support[size][q]) == (364 if size == 2 else 78), "count support")
            model.add(count_vars[size][q] == sum(x[i] for i in support[size][q]))
    for triple, hole in zip(SETS[3], hole_vars, strict=True):
        model.add(count_vars[3][triple] == 0).only_enforce_if(hole)
        model.add(count_vars[3][triple] >= 1).only_enforce_if(hole.Not())
    for triple in SETS[3]:
        for pair in itertools.combinations(triple, 2):
            model.add(3 * count_vars[2][pair] - count_vars[3][triple] >= 13)
    for pair in SETS[2]:
        outside = [a for a in range(1, 17) if a not in pair]
        for a, b in itertools.combinations(outside, 2):
            model.add(
                3 * count_vars[2][pair]
                - count_vars[3][tuple(sorted((*pair, a)))]
                - count_vars[3][tuple(sorted((*pair, b)))]
                + d_vars[pair]
                >= 12
            )
    for core in cores:
        model.add(sum(x[i] for i in core) <= 55)
    model.minimize(561 * sum(d_vars.values()) + sum(hole_vars))
    prior_model = cp_model.CpModel()
    require(
        prior_model.proto.parse_text_format((ROOT / prior["model_path"]).read_text()),
        "prior model parse",
    )
    prior_model.clear_hints()
    require(str(model.proto) == str(prior_model.proto), "model changed beyond the hint")
    unchanged_model_sha = hashlib.sha256(str(model.proto).encode()).hexdigest()
    values = initial["values"]
    require(len(model.proto.variables) == len(values) == 5728, "variable count")
    require(len(model.proto.constraints) == 14405, "constraint count")
    for index, value in enumerate(values):
        model.add_hint(model.get_int_var_from_proto_index(index), value)
    require(not model.validate(), "invalid CP model")
    check = check_vector(model, values)
    require(check["objective"] == 19086, "objective mismatch")
    parameters = cp_model.CpSolver().parameters
    parameters.max_time_in_seconds = 300
    parameters.num_search_workers = 4
    parameters.random_seed = 2026104901
    parameters.log_search_progress = True
    parameters.log_to_stdout = False
    prior_parameters = cp_model.CpSolver().parameters
    require(
        prior_parameters.parse_text_format((ROOT / prior["parameters_path"]).read_text()),
        "prior parameters parse",
    )
    prior_parameters.max_time_in_seconds = 300
    prior_parameters.random_seed = 2026104901
    require(str(parameters) == str(prior_parameters), "parameters changed beyond budget and seed")
    RAW.mkdir(parents=True)
    model_path, parameters_path = RAW / "model.pbtxt", RAW / "parameters.pbtxt"
    model_path.write_text(str(model.proto))
    parameters_path.write_text(str(parameters))
    hint_path = RAW / "complete-h12-hint.json"
    dump(
        hint_path,
        {
            "candidate_sha256": HINT_SHA,
            "values": values,
            "metrics": metrics,
            "pair_details": initial["pair_details"],
            "vector_check": check,
            "global_profile": profile,
            "verification": verification,
        },
    )
    snapshot = RAW / "frozen-sources"
    snapshot.mkdir()
    source_paths = [
        Path(__file__),
        HERE / "execute.py",
        HELPER,
        ROOT / "src/covering64/core.py",
        ROOT / "scripts/check_cover.py",
    ]
    sources = {}
    for source in source_paths:
        require(source.exists(), f"missing source {source}")
        target = snapshot / source.name
        shutil.copy2(source, target)
        sources[str(source.relative_to(ROOT))] = sha(source)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    manifest = {
        "status": "PREPARED; independent GO required; no Solve called",
        "optimizer_calls": 0,
        "input_files": input_files,
        "prior_manifest_sha256": sha(PRIOR / "manifest.json"),
        "prior_gate_sha256": INPUT_BINDINGS["soft-pair-two-independent/gate.json"],
        "unchanged_model_without_hint_sha256": unchanged_model_sha,
        "model_delta": "Only complete solution_hint replaced; all other proto fields identical",
        "parameter_delta": {
            "max_time_in_seconds": [120, 300],
            "random_seed": [2026104302, 2026104901],
        },
        "profile_manifest_sha256": INPUT_BINDINGS["native-partial-start-profiles/manifest.json"],
        "profile_diagnostic_sha256": INPUT_BINDINGS[
            "native-partial-start-profiles/diagnostic.json"
        ],
        "source_revision": revision,
        "source_sha256": sha(__file__),
        "sources": sources,
        "ortools_version": ortools.__version__,
        "python_version": platform.python_version(),
        "raw_directory": str(RAW.relative_to(ROOT)),
        "model_path": str(model_path.relative_to(ROOT)),
        "model_sha256": sha(model_path),
        "parameters_path": str(parameters_path.relative_to(ROOT)),
        "parameters_sha256": sha(parameters_path),
        "hint_path": str(hint_path.relative_to(ROOT)),
        "hint_sha256": sha(hint_path),
        "candidate_path": str(HINT.relative_to(ROOT)),
        "candidate_sha256": HINT_SHA,
        "variables": 5728,
        "constraints": 14405,
        "full_hint_entries": len(model.proto.solution_hint.vars),
        "hint_metrics": metrics,
        "hint_vector_check": check,
        "core_rows": cores,
        "frozen_proofs": helper.FROZEN,
        "budget_seconds": 300,
        "workers": 4,
        "seed": 2026104901,
        "objective": "561*sum(d_P)+holes; no core tie-break",
        "variable_order": {
            "blocks": [0, 4367],
            "pairs": [4368, 4487],
            "triples": [4488, 5047],
            "holes": [5048, 5607],
            "d": [5608, 5727],
        },
        "restrictions": [
            "exactly 64",
            "pair floor 5",
            "1680 single-triple cuts",
            "four core caps 55",
        ],
        "soft_rows": 10920,
        "deficit_domain": [0, 128],
        "not_imposed": ["degree20", "symmetry", "restricted family", "global profile", "hard D2"],
        "scope": "cover-preserving search; not an independently proved global lower bound",
    }
    dump(HERE / "manifest.json", manifest)
    dump(
        HERE / "preparation.json",
        {
            "passed": True,
            "optimizer_calls": 0,
            "vector_check": check,
            "metrics": metrics,
            "global_profile": profile,
            "manifest_sha256": sha(HERE / "manifest.json"),
        },
    )
    print(
        json.dumps(
            {
                "prepared": True,
                "optimizer_calls": 0,
                "variables": 5728,
                "rows": 14405,
                "hint_objective": 19086,
                "manifest_sha256": sha(HERE / "manifest.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
