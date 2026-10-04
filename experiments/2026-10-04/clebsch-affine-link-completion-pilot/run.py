# Document:    Seven Conditional Clebsch Affine Link Completion Pilots
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      4b16250043423665d17c2d6e4343d4dac6d1360eddbc09eee858539e21dda868
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare exact models; root may run seven bounded calls after independent GO."""

from __future__ import annotations

import importlib.util
import json
import os
import platform
import signal
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
RAW = ROOT / "experiments/scratch/clebsch-affine-link-completion-v1.0.0"
CONSTRUCTION = HERE.parent / "clebsch-point-link-construction"
SCREEN = HERE.parent / "clebsch-affine-link-support-screen"
PROFILE = ROOT / (
    "experiments/2026-10-03/independent-geometry/independent-audit-seed-profiles.json"
)
BLOCKS = tuple(combinations(range(1, 17), 5))
RANK = {block: index for index, block in enumerate(BLOCKS)}
TRIPLES = tuple(combinations(range(1, 17), 3))
CASE_PAIRS = [(0, 10), (40, 13), (4, 7), (18, 3), (16, 3), (16, 8), (60, 3)]
SEEDS = list(range(2026106301, 2026106308))
SECONDS = 30.0
WORKERS = 1
WATCHDOG = 35.0
GRACE = 5.0


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def canonical_bytes(rows):
    return "".join(" ".join(map(str, row)) + "\n" for row in sorted(rows)).encode("ascii")


def relative(path):
    return str(path.relative_to(ROOT))


def dual(witness):
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    spec = importlib.util.spec_from_file_location(
        "standalone_cover_check", ROOT / "scripts/check_cover.py"
    )
    standalone = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(standalone)
    return verify_cover(witness), standalone.verify_cover(witness, expected_blocks=len(witness))


def parameters(seed):
    params = cp_model.CpSolver().parameters
    params.max_time_in_seconds = SECONDS
    params.num_search_workers = WORKERS
    params.random_seed = seed
    params.log_search_progress = True
    params.log_to_stdout = True
    return params


def prepare():
    require(not (HERE / "manifest.json").exists() and not RAW.exists(), "fresh preparation only")
    profiles = json.loads(PROFILE.read_text())
    classes = json.loads((CONSTRUCTION / "classes.json").read_text())
    links = json.loads((CONSTRUCTION / "recipe-point-maps.json").read_text())
    survivors = json.loads((SCREEN / "summary.json").read_text())["survivors"]
    require(
        [(row["profile_seed"], row["point"]) for row in survivors] == CASE_PAIRS,
        "seven pinned survivors",
    )
    containing = {triple: [] for triple in TRIPLES}
    for index, block in enumerate(BLOCKS):
        for triple in combinations(block, 3):
            containing[triple].append(index)
    require(
        len(BLOCKS) == 4368 and all(len(ids) == 78 for ids in containing.values()),
        "full incidence matrix",
    )
    RAW.mkdir(parents=True)
    prepared = []
    cases = []
    for number, ((profile_seed, point), seed) in enumerate(zip(CASE_PAIRS, SEEDS), 1):
        link = next(
            row for row in links if row["profile_seed"] == profile_seed and row["point"] == point
        )
        profile = {tuple(row) for row in profiles[str(profile_seed)]}
        local = [
            tuple(sorted(link["canonical_to_actual"][x - 1] for x in block))
            for block in classes[link["class"]]["canonical_blocks"]
        ]
        witness = sorted(tuple(sorted((point, *block))) for block in local)
        require(
            sha256(canonical_bytes(witness)).hexdigest() == link["partial_canonical_sha256"],
            "partial pin",
        )
        package, standalone = dual(witness)
        require(package["covered"] == standalone["covered_subsets"] == 185, "partial coverage")
        require(package["blocks"] == standalone["blocks"] == 20, "partial cardinality")
        require(not package["valid"] and not standalone["valid"], "partial is not full cover")
        selected = {RANK[block] for block in witness}
        fixed = [index for index, block in enumerate(BLOCKS) if point in block]
        require(len(fixed) == 1365 and len(selected) == 20, "all point memberships fixed")
        model = cp_model.CpModel()
        variables = [model.new_bool_var(f"block_{index}") for index in range(4368)]
        for triple in TRIPLES:
            model.add(
                sum(variables[index] for index in containing[triple]) == 1 + (triple in profile)
            )
        model.add(sum(variables) == 64)
        for index in fixed:
            model.add(variables[index] == int(index in selected))
        require(len(model.proto.variables) == 4368, "full binary variable set")
        require(
            len(model.proto.constraints) == 1926 and not model.validate(), "valid full model rows"
        )
        case_raw = RAW / f"case-{number}"
        case_raw.mkdir()
        model_path = case_raw / "model.pbtxt"
        parameter_path = case_raw / "parameters.pbtxt"
        model_path.write_text(str(model.proto))
        parameter_path.write_text(str(parameters(seed)))
        witness_path = HERE / f"case-{number}-partial.txt"
        witness_path.write_bytes(canonical_bytes(witness))
        profile_path = HERE / f"case-{number}-profile.json"
        dump(profile_path, sorted(profile))
        local_counts = Counter(triple for block in local for triple in combinations(block, 3))
        residual_rows = [
            {"triple": triple, "demand": 1 + (triple in profile) - local_counts[triple]}
            for triple in TRIPLES
            if point not in triple
        ]
        require(
            len(residual_rows) == 455 and sum(row["demand"] for row in residual_rows) == 440,
            "residual rows",
        )
        require(all(row["demand"] >= 0 for row in residual_rows), "nonnegative residuals")
        residual_path = HERE / f"case-{number}-residual.json"
        dump(residual_path, residual_rows)
        checks_path = HERE / f"case-{number}-partial-verification.json"
        dump(checks_path, {"package": package, "standalone": standalone})
        prepared.extend(
            [model_path, parameter_path, witness_path, profile_path, residual_path, checks_path]
        )
        cases.append(
            {
                "case": number,
                "profile_seed": profile_seed,
                "point": point,
                "class": link["class"],
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
                "fixed_point_memberships": len(fixed),
                "fixed_selected": len(selected),
                "initially_free_avoiding_point": 3003,
                "remaining_selected": 44,
                "zero_residual_rows": sum(row["demand"] == 0 for row in residual_rows),
            }
        )
    dependencies = [
        PROFILE,
        CONSTRUCTION / "classes.json",
        CONSTRUCTION / "recipe-point-maps.json",
        CONSTRUCTION / "files.json",
        SCREEN / "summary.json",
        SCREEN / "cases.json",
        SCREEN / "files.json",
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
            "dependencies": {relative(path): sha(path) for path in dependencies},
            "prepared_files": {relative(path): sha(path) for path in prepared},
            "cases": cases,
            "variables": 4368,
            "global_exact_triple_rows": 560,
            "cardinality_rows": 1,
            "fixed_membership_rows": 1365,
            "total_rows": 1926,
            "variable_order": "All C(16,5) blocks in lexicographic order, zero-based IDs.",
            "search_launches_during_preparation": 0,
            "max_calls": 7,
            "total_solver_budget_seconds": 210,
            "retry_or_budget_transfer": False,
            "objective": None,
            "hints": None,
            "propagation_pruning_used_to_restrict_model": False,
            "scope": (
                "Seven exact64 completion models, each fixed to one saved20-block "
                "affine point link "
                "and one recipe excess profile. No other point-avoiding memberships fixed. "
                "No global nonexistence conclusion from any result."
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
    require(sha(__file__) == manifest["source_sha256"], "frozen runner hash")
    require(ortools.__version__ == manifest["ortools_version"], "solver version pin")
    for field in ("dependencies", "prepared_files"):
        for path, expected in manifest[field].items():
            require(sha(ROOT / path) == expected, f"frozen file: {path}")
    require(len(manifest["cases"]) == 7, "seven cases")
    for case, pair, seed in zip(manifest["cases"], CASE_PAIRS, SEEDS):
        require(
            (case["profile_seed"], case["point"]) == pair and case["seed"] == seed,
            "case ordering and seed",
        )
        require(
            (case["seconds"], case["workers"], case["watchdog_seconds"], case["grace_seconds"])
            == (SECONDS, WORKERS, WATCHDOG, GRACE),
            "fixed budgets",
        )
    return manifest


def worker(number):
    manifest = check_pins()
    require((HERE / "run-started.json").exists(), "root wrapper launch record required")
    require(1 <= number <= 7, "case range")
    case = manifest["cases"][number - 1]
    destination = HERE / f"case-{number}-output"
    destination.mkdir(exist_ok=False)
    model = cp_model.CpModel()
    require(model.proto.parse_text_format((ROOT / case["model"]).read_text()), "model parse")
    require(not model.validate(), "model validation before solve")
    solver = cp_model.CpSolver()
    require(
        solver.parameters.parse_text_format((ROOT / case["parameters"]).read_text()),
        "parameters parse",
    )
    require(str(solver.parameters) == str(parameters(case["seed"])), "exact solver parameters")
    started = time.monotonic()
    status = solver.solve(model)
    result = {
        "case": number,
        "profile_seed": case["profile_seed"],
        "point": case["point"],
        "seed": case["seed"],
        "status": solver.status_name(status),
        "solver_wall_time_seconds": solver.wall_time,
        "elapsed_seconds": time.monotonic() - started,
        "branches": solver.num_branches,
        "conflicts": solver.num_conflicts,
        "response_stats": solver.response_stats(),
        "proof_generated": False,
        "global_nonexistence_claim": False,
        "scope": "This exact pinned partial and fixed excess profile only.",
        "status_note": (
            "UNKNOWN is inconclusive; INFEASIBLE lacks an independent proof certificate."
        ),
        "source_revision": manifest["source_revision"],
        "manifest_sha256": sha(HERE / "manifest.json"),
        "model_sha256": sha(ROOT / case["model"]),
        "parameters_sha256": sha(ROOT / case["parameters"]),
        "ortools_version": ortools.__version__,
        "python_version": platform.python_version(),
        "witness": None,
    }
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        values = [solver.value(model.get_bool_var_from_proto_index(index)) for index in range(4368)]
        selected = [block for block, value in zip(BLOCKS, values) if value]
        require(len(selected) == 64 and set(values) <= {0, 1}, "binary exact64 result")
        profile = {tuple(row) for row in json.loads((ROOT / case["profile"]).read_text())}
        counts = Counter(triple for block in selected for triple in combinations(block, 3))
        require(
            all(counts[triple] == 1 + (triple in profile) for triple in TRIPLES),
            "full exact demand check",
        )
        partial = [
            tuple(map(int, line.split()))
            for line in (ROOT / case["partial"]).read_text().splitlines()
        ]
        require(
            [block for block in selected if case["point"] in block] == partial,
            "all fixed memberships",
        )
        package, standalone = dual(selected)
        require(package["valid"] and standalone["valid"], "both cover verifiers")
        require(
            package["canonical_sha256"] == standalone["canonical_sha256"], "both canonical hashes"
        )
        witness_path = destination / "witness.txt"
        witness_path.write_bytes(canonical_bytes(selected))
        dump(destination / "values.json", values)
        dump(destination / "package-verification.json", package)
        dump(destination / "standalone-verification.json", standalone)
        result["witness"] = {"path": relative(witness_path), "sha256": sha(witness_path)}
    dump(destination / "result.json", result)


def terminate_group(process, sig):
    try:
        os.killpg(process.pid, sig)
    except ProcessLookupError:
        pass


def bounded_child(command, stdout, stderr):
    started = time.monotonic()
    process = subprocess.Popen(
        command, cwd=ROOT, stdout=stdout, stderr=stderr, start_new_session=True
    )
    watchdog_fired = False
    kill_required = False
    try:
        code = process.wait(timeout=WATCHDOG)
    except subprocess.TimeoutExpired:
        watchdog_fired = True
        terminate_group(process, signal.SIGTERM)
        try:
            code = process.wait(timeout=GRACE)
        except subprocess.TimeoutExpired:
            kill_required = True
            terminate_group(process, signal.SIGKILL)
            code = process.wait()
    return {
        "returncode": code,
        "watchdog_fired": watchdog_fired,
        "kill_required": kill_required,
        "elapsed_seconds": time.monotonic() - started,
        "watchdog_seconds": WATCHDOG,
        "grace_seconds": GRACE,
    }


def run():
    manifest = check_pins()
    require(not any(HERE.glob("case-*-output")), "fresh outputs only")
    descriptor = os.open(HERE / "run-started.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        json.dump({"manifest_sha256": sha(HERE / "manifest.json"), "max_calls": 7}, handle)
        handle.write("\n")
    receipts = []
    for case in manifest["cases"]:
        check_pins()
        number = case["case"]
        stdout_path = HERE / f"case-{number}-stdout.log"
        stderr_path = HERE / f"case-{number}-stderr.log"
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            receipt = bounded_child(
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
                "complete": len(receipts) == 7,
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
        raise SystemExit("Usage: run.py prepare|run|_worker CASE")
