# Document:    Four Conditional Completions of Circulant Survivor Links
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      f4a6c8867457431233712fe6477a1b579144726a19bd22725e04b88e8718caae
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare selected full-domain models; only root may launch after independent review."""

from __future__ import annotations

import gzip
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/circulant-survivor-completion-pilot-v1.0.0"
CATALOG = HERE.parent / "circulant-chosen-link-catalog"
PROPAGATION = HERE.parent / "circulant-chosen-link-row-propagation-full"
PROPAGATION_REVIEW = (
    HERE.parent / "circulant-chosen-link-row-propagation-full-runtime-independent/review.json"
)
PROPAGATION_REVIEW_SHA = "aceba1e0c1280be6154950dfe61e5545ff40035cb5307e3749b1ac97c630f92a"
ORBIT = HERE.parent / "circulant-all-excess-independent"
HELPER = HERE.parent / "clebsch-affine-link-completion-pilot/run.py"
HELPER_SHA = "a98252d012008a3c17d45b553783b564ecb0547509a88535eb37f800d4e2f316"
RESULT_SHA = "05a05fb907ad2b5e425977939e04ddb5c599abfa6dc9c4c203da2f9b76de6db2"
SURVIVOR_SHA = "60e42a6855fc897130c80d8db8189cd9639e0981555386e5938ed02a5eda90ed"
ORBITS_SHA = "d0aab8d3de76e07c23a71adb10d10b36e403275fd236f52522f38e0efac480d6"
SEEDS = list(range(2026106701, 2026106705))
SECONDS = 30.0
WORKERS = 1
WATCHDOG = 35.0
GRACE = 5.0
BLOCKS = tuple(combinations(range(1, 17), 5))
TRIPLES = tuple(combinations(range(1, 17), 3))
RANK = {block: index for index, block in enumerate(BLOCKS)}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def relative(path):
    return str(path.relative_to(ROOT))


def helper():
    require(sha(HELPER) == HELPER_SHA, "frozen helper source")
    spec = importlib.util.spec_from_file_location("frozen_completion_helpers", HELPER)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    require(
        (loaded.SECONDS, loaded.WORKERS, loaded.WATCHDOG, loaded.GRACE)
        == (SECONDS, WORKERS, WATCHDOG, GRACE),
        "unchanged helper budgets",
    )
    return loaded


def load_selection():
    require(sha(PROPAGATION_REVIEW) == PROPAGATION_REVIEW_SHA, "full replay audit pin")
    replay = json.loads(PROPAGATION_REVIEW.read_text())
    require(
        replay["passed"]
        and replay["complete"]
        and replay["completed_cases"] == 10228
        and replay["result_sha256"] == RESULT_SHA,
        "accepted full propagation replay",
    )
    require(sha(PROPAGATION / "result.json") == RESULT_SHA, "full propagation result pin")
    result = json.loads((PROPAGATION / "result.json").read_text())
    require(
        result["complete"]
        and result["completed_cases"] == 10228
        and result["outcomes"] == {"contradiction": 9132, "survives_row_propagation": 1096},
        "complete finite propagation pass",
    )
    survivor_path = ROOT / result["survivor_records_path"]
    require(
        sha(survivor_path) == result["survivor_records_sha256"] == SURVIVOR_SHA,
        "survivor stream pin",
    )
    with gzip.open(survivor_path, "rt") as handle:
        records = [json.loads(line) for line in handle]
    require(len(records) == 1096, "all saved unresolved cases")
    partials = json.loads((CATALOG / "partial-catalog.json").read_text())
    profiles = json.loads((CATALOG / "profiles.json").read_text())
    fibers = json.loads((CATALOG / "link-fibers.json").read_text())
    require(sha(ORBIT / "orbits.json") == ORBITS_SHA, "audited profile orbit pin")
    orbits = json.loads((ORBIT / "orbits.json").read_text())
    orbit_by_mask = {mask: row["representative_mask"] for row in orbits for mask in row["members"]}
    require(len(orbit_by_mask) == 1300 and len(orbits) == 52, "complete audited orbit partition")
    automorphisms = json.loads((ORBIT / "automorphisms.json").read_text())
    stabilizer = automorphisms["stabilizer"]
    require(
        stabilizer == [list(range(1, 17)), [1, *range(16, 1, -1)]],
        "audited identity and point-one reflection",
    )
    partial_ids = {tuple(row["global_block_ids"]): row["partial_id"] for row in partials}
    profile_ids = {
        tuple(tuple(t) for t in row["excess_triples"]): row["profile_id"] for row in profiles
    }
    by_pair = {(row["partial_id"], row["profile_id"]): row for row in records}
    require(len(by_pair) == len(records), "distinct saved pairs")
    reflection = stabilizer[1]
    block_reflection = [RANK[tuple(sorted(reflection[p - 1] for p in b))] for b in BLOCKS]
    reflection_groups = {}
    for row in records:
        partial = partials[row["partial_id"]]
        profile = profiles[row["profile_id"]]
        fiber = fibers[partial["excess_link_id"]]
        require(row["profile_id"] in fiber["profile_ids"], "compatible fiber identity")
        row["class"] = fiber["class"]
        row["free_variables_after_propagation"] = (
            3003 - row["selected_count"] - row["removed_count"]
        )
        require(row["free_variables_after_propagation"] >= 0, "valid free count")
        row["profile_orbit_representative_mask"] = orbit_by_mask[profile["choice_mask"]]
        mapped_partial = tuple(sorted(block_reflection[i] for i in partial["global_block_ids"]))
        mapped_profile = tuple(
            sorted(tuple(sorted(reflection[p - 1] for p in t)) for t in profile["excess_triples"])
        )
        reflected_key = (partial_ids[mapped_partial], profile_ids[mapped_profile])
        require(reflected_key in by_pair, "reflected case remains in survivor set")
        reflected = by_pair[reflected_key]
        require(
            row["selected_count"] == reflected["selected_count"]
            and row["removed_count"] == reflected["removed_count"],
            "reflection preserves fixed-point free count",
        )
        representative = min(row["pair_ordinal"], reflected["pair_ordinal"])
        row["reflection_representative_pair_ordinal"] = representative
        row["reflected_pair_ordinal"] = reflected["pair_ordinal"]
        reflection_groups.setdefault(representative, set()).add(row["pair_ordinal"])

    def rank(row):
        return (row["free_variables_after_propagation"], row["pair_ordinal"])

    core_types = sorted({row["class"] for row in records})
    require(len(core_types) == 3, "three available core types for this frozen selection")
    selected = [min((r for r in records if r["class"] == core), key=rank) for core in core_types]
    used_orbits = {r["profile_orbit_representative_mask"] for r in selected}
    used_reflections = {r["reflection_representative_pair_ordinal"] for r in selected}
    additional = [
        r for r in records if r["reflection_representative_pair_ordinal"] not in used_reflections
    ]
    novel_orbit = [
        r for r in additional if r["profile_orbit_representative_mask"] not in used_orbits
    ]
    require(additional, "a fourth nonequivalent case exists")
    selected.append(min(novel_orbit or additional, key=rank))
    require(
        len({r["reflection_representative_pair_ordinal"] for r in selected}) == 4,
        "four reflection-inequivalent selections",
    )
    selection = {
        "input_survivor_count": 1096,
        "core_type_counts": dict(sorted(Counter(r["class"] for r in records).items())),
        "reflection_orbit_count": len(reflection_groups),
        "reflection_orbit_size_counts": dict(
            sorted(Counter(map(len, reflection_groups.values())).items())
        ),
        "reflection_groups": [sorted(reflection_groups[k]) for k in sorted(reflection_groups)],
        "selection_rule": (
            "Minimum (free count, pair ordinal) per sorted available core type; then minimum "
            "from a new profile orbit if possible, excluding used reflection orbits"
        ),
        "fourth_case_uses_new_profile_orbit": bool(novel_orbit),
        "selected": selected,
        "purpose_of_propagation_counts": "Selection only; never restrictions or hints in the model",
        "scope": "Four selected conditional attempts; not exhaustive survivor coverage",
    }
    return selection, partials, profiles, survivor_path, result


def prepare():
    require(not (HERE / "manifest.json").exists() and not RAW.exists(), "fresh preparation")
    utility = helper()
    audit = json.loads((HERE / "seed-audit.json").read_text())
    require(audit["seeds"] == SEEDS and not audit["hits"], "unused seed audit")
    selection, partials, profiles, survivor_path, propagation = load_selection()
    dump(HERE / "selection.json", selection)
    containing = {triple: [] for triple in TRIPLES}
    for index, block in enumerate(BLOCKS):
        for triple in combinations(block, 3):
            containing[triple].append(index)
    require(
        len(BLOCKS) == 4368 and all(len(ids) == 78 for ids in containing.values()),
        "full lexicographic incidence matrix",
    )
    fixed = [i for i, block in enumerate(BLOCKS) if 1 in block]
    require(fixed == list(range(1365)), "all point-one variables")
    RAW.mkdir(parents=True)
    prepared = [HERE / "selection.json"]
    cases = []
    for number, (record, seed) in enumerate(zip(selection["selected"], SEEDS), 1):
        partial = partials[record["partial_id"]]
        profile = {tuple(t) for t in profiles[record["profile_id"]]["excess_triples"]}
        require(len(profile) == 80, "exact80 profile")
        selected = set(partial["global_block_ids"])
        witness = [BLOCKS[i] for i in sorted(selected)]
        require(len(selected) == 20 and selected <= set(fixed), "chosen20 point-one blocks")
        require(
            sha256(utility.canonical_bytes(witness)).hexdigest()
            == partial["partial_canonical_sha256"],
            "chosen partial canonical hash",
        )
        package, standalone = utility.dual(witness)
        require(package["covered"] == standalone["covered_subsets"] == 185, "partial coverage")
        require(package["blocks"] == standalone["blocks"] == 20, "partial cardinality")
        require(not package["valid"] and not standalone["valid"], "partial is not a full cover")
        model = cp_model.CpModel()
        variables = [model.new_bool_var(f"block_{i}") for i in range(4368)]
        for triple in TRIPLES:
            model.add(sum(variables[i] for i in containing[triple]) == 1 + (triple in profile))
        model.add(sum(variables) == 64)
        for index in fixed:
            model.add(variables[index] == int(index in selected))
        require(
            len(model.proto.variables) == 4368 and len(model.proto.constraints) == 1926,
            "full variables and exactly requested equations",
        )
        require(not model.validate(), "model validation without solve")
        case_raw = RAW / f"case-{number}"
        case_raw.mkdir()
        model_path = case_raw / "model.pbtxt"
        parameter_path = case_raw / "parameters.pbtxt"
        model_path.write_text(str(model.proto))
        parameter_path.write_text(str(utility.parameters(seed)))
        witness_path = HERE / f"case-{number}-partial.txt"
        witness_path.write_bytes(utility.canonical_bytes(witness))
        profile_path = HERE / f"case-{number}-profile.json"
        dump(profile_path, sorted(profile))
        partial_counts = Counter(t for block in witness for t in combinations(block, 3))
        require(
            all(partial_counts[t] == 1 + (t in profile) for t in TRIPLES if 1 in t),
            "all105 pinned point-one triple equations",
        )
        residual = [
            {"triple": t, "demand": 1 + (t in profile) - partial_counts[t]}
            for t in TRIPLES
            if 1 not in t
        ]
        require(
            len(residual) == 455
            and sum(r["demand"] for r in residual) == 440
            and min(r["demand"] for r in residual) >= 0,
            "exact residual accounting",
        )
        residual_path = HERE / f"case-{number}-residual.json"
        dump(residual_path, residual)
        checks_path = HERE / f"case-{number}-partial-verification.json"
        dump(checks_path, {"package": package, "standalone": standalone})
        prepared.extend(
            [model_path, parameter_path, witness_path, profile_path, residual_path, checks_path]
        )
        cases.append(
            {
                **record,
                "case": number,
                "point": 1,
                "seed": seed,
                "seconds": SECONDS,
                "workers": WORKERS,
                "watchdog_seconds": WATCHDOG,
                "grace_seconds": GRACE,
                "model": relative(model_path),
                "parameters": relative(parameter_path),
                "partial": relative(witness_path),
                "profile": relative(profile_path),
                "residual": relative(residual_path),
                "partial_sha256": sha(witness_path),
                "fixed_point_memberships": 1365,
                "fixed_selected": 20,
                "initially_free_avoiding_point": 3003,
                "remaining_selected": 44,
            }
        )
    dependencies = [
        HELPER,
        PROPAGATION / "run.py",
        PROPAGATION / "manifest.json",
        PROPAGATION / "result.json",
        PROPAGATION / "execution.json",
        PROPAGATION_REVIEW,
        PROPAGATION_REVIEW.parent / "files.json",
        survivor_path,
        ROOT / propagation["proof_records"],
        CATALOG / "partial-catalog.json",
        CATALOG / "profiles.json",
        CATALOG / "link-fibers.json",
        CATALOG / "files.json",
        ORBIT / "orbits.json",
        ORBIT / "automorphisms.json",
        ORBIT / "audit.json",
        ROOT / "scripts/check_cover.py",
        ROOT / "src/covering64/core.py",
        ROOT / "uv.lock",
        HERE / "README.md",
        HERE / "seed-audit.json",
    ]
    dump(
        HERE / "manifest.json",
        {
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "source_sha256": sha(__file__),
            "python_version": platform.python_version(),
            "ortools_version": ortools.__version__,
            "dependencies": {relative(p): sha(p) for p in dependencies},
            "prepared_files": {relative(p): sha(p) for p in prepared},
            "cases": cases,
            "variables": 4368,
            "global_exact_triple_rows": 560,
            "cardinality_rows": 1,
            "fixed_membership_rows": 1365,
            "total_rows": 1926,
            "variable_order": "All C(16,5) blocks in lexicographic order, zero-based IDs",
            "search_launches_during_preparation": 0,
            "max_calls": 4,
            "total_solver_budget_seconds": 120,
            "retry_or_budget_transfer": False,
            "objective": None,
            "hints": None,
            "cover_invariance": None,
            "propagation_pruning_used_to_restrict_model": False,
            "selection_only_reflection_deduplication": True,
            "scope": (
                "Four selected conditional completions of chosen point-one links and fixed "
                "excess profiles. Not exhaustive survivor coverage and not a global "
                "nonexistence proof."
            ),
        },
    )
    print(
        json.dumps(
            {
                "prepared": True,
                "manifest_sha256": sha(HERE / "manifest.json"),
                "optimizer_launches": 0,
            }
        )
    )


def check_pins():
    manifest = json.loads((HERE / "manifest.json").read_text())
    require(sha(__file__) == manifest["source_sha256"], "frozen runner source")
    require(ortools.__version__ == manifest["ortools_version"], "solver version pin")
    for field in ("dependencies", "prepared_files"):
        for path, expected in manifest[field].items():
            require(sha(ROOT / path) == expected, f"frozen input: {path}")
    require(len(manifest["cases"]) == 4, "four calls")
    for number, (case, seed) in enumerate(zip(manifest["cases"], SEEDS), 1):
        require(case["case"] == number and case["seed"] == seed, "fixed case and seed order")
        require(
            (case["seconds"], case["workers"], case["watchdog_seconds"], case["grace_seconds"])
            == (SECONDS, WORKERS, WATCHDOG, GRACE),
            "fixed budgets",
        )
    return manifest


def worker(number):
    manifest = check_pins()
    launch = json.loads((HERE / "run-started.json").read_text())
    require(launch["supervisor_pid"] == os.getppid(), "sole supervisor parent")
    require(launch["manifest_sha256"] == sha(HERE / "manifest.json"), "launch manifest")
    require(1 <= number <= 4, "case range")
    case = manifest["cases"][number - 1]
    destination = HERE / f"case-{number}-output"
    destination.mkdir(exist_ok=False)
    utility = helper()
    model = cp_model.CpModel()
    require(model.proto.parse_text_format((ROOT / case["model"]).read_text()), "model parse")
    require(not model.validate(), "model validation before solve")
    solver = cp_model.CpSolver()
    require(
        solver.parameters.parse_text_format((ROOT / case["parameters"]).read_text()),
        "parameters parse",
    )
    require(str(solver.parameters) == str(utility.parameters(case["seed"])), "exact parameters")
    started = time.monotonic()
    status = solver.solve(model)
    result = {
        "case": number,
        "pair_ordinal": case["pair_ordinal"],
        "partial_id": case["partial_id"],
        "profile_id": case["profile_id"],
        "class": case["class"],
        "point": 1,
        "seed": case["seed"],
        "status": solver.status_name(status),
        "solver_wall_time_seconds": solver.wall_time,
        "elapsed_seconds": time.monotonic() - started,
        "branches": solver.num_branches,
        "conflicts": solver.num_conflicts,
        "response_stats": solver.response_stats(),
        "proof_generated": False,
        "global_nonexistence_claim": False,
        "scope": "This selected pinned partial and fixed excess profile only",
        "status_note": "UNKNOWN is inconclusive; INFEASIBLE lacks an independently checked proof",
        "source_revision": manifest["source_revision"],
        "manifest_sha256": sha(HERE / "manifest.json"),
        "model_sha256": sha(ROOT / case["model"]),
        "parameters_sha256": sha(ROOT / case["parameters"]),
        "ortools_version": ortools.__version__,
        "python_version": platform.python_version(),
        "witness": None,
    }
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        values = [solver.value(model.get_bool_var_from_proto_index(i)) for i in range(4368)]
        chosen = [block for block, value in zip(BLOCKS, values) if value]
        require(len(chosen) == 64 and set(values) <= {0, 1}, "binary exact64 result")
        profile = {tuple(t) for t in json.loads((ROOT / case["profile"]).read_text())}
        counts = Counter(t for block in chosen for t in combinations(block, 3))
        require(all(counts[t] == 1 + (t in profile) for t in TRIPLES), "all exact560 demands")
        partial = [
            tuple(map(int, line.split()))
            for line in (ROOT / case["partial"]).read_text().splitlines()
        ]
        require([block for block in chosen if 1 in block] == partial, "all fixed memberships")
        package, standalone = utility.dual(chosen)
        require(package["valid"] and standalone["valid"], "both full cover verifiers")
        require(package["canonical_sha256"] == standalone["canonical_sha256"], "canonical hashes")
        witness_path = destination / "witness.txt"
        witness_path.write_bytes(utility.canonical_bytes(chosen))
        dump(destination / "values.json", values)
        dump(destination / "package-verification.json", package)
        dump(destination / "standalone-verification.json", standalone)
        result["witness"] = {"path": relative(witness_path), "sha256": sha(witness_path)}
    dump(destination / "result.json", result)


def run():
    manifest = check_pins()
    require(not any(HERE.glob("case-*-output")), "fresh outputs only")
    descriptor = os.open(HERE / "run-started.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        json.dump(
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "max_calls": 4,
                "supervisor_pid": os.getpid(),
            },
            handle,
        )
        handle.write("\n")
    utility = helper()
    receipts = []
    for case in manifest["cases"]:
        check_pins()
        number = case["case"]
        stdout_path = HERE / f"case-{number}-stdout.log"
        stderr_path = HERE / f"case-{number}-stderr.log"
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            receipt = utility.bounded_child(
                [sys.executable, str(Path(__file__).resolve()), "_worker", str(number)],
                stdout,
                stderr,
            )
        receipt.update(
            {"case": number, "stdout_sha256": sha(stdout_path), "stderr_sha256": sha(stderr_path)}
        )
        result_path = HERE / f"case-{number}-output/result.json"
        receipt["result_sha256"] = sha(result_path) if result_path.exists() else None
        receipts.append(receipt)
        dump(
            HERE / "runtime.json",
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "calls": receipts,
                "complete": len(receipts) == 4,
            },
        )
        print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["prepare"]:
        prepare()
    elif sys.argv[1:] == ["run"]:
        run()
    elif len(sys.argv) == 3 and sys.argv[1] == "_worker":
        worker(int(sys.argv[2]))
    else:
        raise SystemExit("Usage: run.py prepare|run; _worker is supervisor-only")
