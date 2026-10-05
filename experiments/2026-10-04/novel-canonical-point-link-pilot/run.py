# Document:    Four Searches for New Canonical Point Link Witnesses
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      517bdcdeba02c667a205cd1b3304b03f2a287f3929d51e2ce85b3eeaba0c618e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare four restricted local models; root alone launches after independent GO."""

from __future__ import annotations

import importlib.util
import json
import os
import platform
import subprocess
import sys
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/novel-canonical-point-link-v1.0.0"
CATALOG = HERE.parent / "circulant-chosen-link-catalog"
CLASSES = HERE.parent / "clebsch-point-link-construction/classes.json"
CATALOG_AUDIT = HERE.parent / "circulant-chosen-link-independent/catalog-audit.json"
BASE = HERE.parent / "clebsch-affine-link-completion-pilot/run.py"
BASE_SHA = "a98252d012008a3c17d45b553783b564ecb0547509a88535eb37f800d4e2f316"
NAMES = ["C4-leaf", "C5", "triangle-path2", "triangle-two-leaves"]
OLD_COUNTS = [96, 320, 96, 144]
SEEDS = list(range(2026106601, 2026106605))
SECONDS = 30.0
WORKERS = 1
QUADS = tuple(combinations(range(1, 16), 4))
QUAD_IDS = {block: index for index, block in enumerate(QUADS)}
PAIRS = tuple(combinations(range(1, 16), 2))
TRIPLES = tuple(combinations(range(1, 16), 3))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def text_bytes(rows):
    return "".join(" ".join(map(str, row)) + "\n" for row in sorted(rows)).encode("ascii")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def dual(blocks, v, k, t):
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    standalone = module(ROOT / "scripts/check_cover.py", "standalone_cover_checker")
    package = verify_cover(blocks, v=v, k=k, t=t)
    independent = standalone.verify_cover(blocks, v=v, k=k, t=t, expected_blocks=20)
    require(package["blocks"] == independent["blocks"] == 20, "dual twenty-block count")
    require(package["canonical_sha256"] == independent["canonical_sha256"], "dual canonical hash")
    return package, independent


def parameters(seed):
    params = cp_model.CpSolver().parameters
    params.max_time_in_seconds = SECONDS
    params.num_search_workers = WORKERS
    params.random_seed = seed
    params.log_search_progress = True
    params.log_to_stdout = True
    return params


def violations(model, values):
    invalid = []
    for index, constraint in enumerate(model.proto.constraints):
        row = constraint.linear
        total = sum(values[var] * coefficient for var, coefficient in zip(row.vars, row.coeffs))
        if not any(
            row.domain[i] <= total <= row.domain[i + 1] for i in range(0, len(row.domain), 2)
        ):
            invalid.append(index)
    return invalid


def prepare():
    require(not (HERE / "manifest.json").exists() and not RAW.exists(), "fresh preparation")
    require(sha(BASE) == BASE_SHA, "frozen watchdog source")
    catalog_audit = json.loads(CATALOG_AUDIT.read_text())
    require(catalog_audit["passed"] is True, "old image catalog independently checked")
    classes = json.loads(CLASSES.read_text())
    images = json.loads((CATALOG / "canonical-images.json").read_text())
    fibers = json.loads((CATALOG / "link-fibers.json").read_text())
    profiles = json.loads((CATALOG / "profiles.json").read_text())
    pair_support = {pair: [] for pair in PAIRS}
    triple_support = {triple: [] for triple in TRIPLES}
    for index, block in enumerate(QUADS):
        for pair in combinations(block, 2):
            pair_support[pair].append(index)
        for triple in combinations(block, 3):
            triple_support[triple].append(index)
    require(
        len(QUADS) == 1365 and all(len(s) == 78 for s in pair_support.values()),
        "full pair incidence",
    )
    require(all(len(s) == 12 for s in triple_support.values()), "full triple incidence")
    RAW.mkdir(parents=True)
    cases = []
    prepared = []
    controls = []
    for number, (name, old_count, seed) in enumerate(zip(NAMES, OLD_COUNTS, SEEDS), 1):
        excess = {tuple(edge) for edge in classes[name]["canonical_excess_edges"]}
        old = [
            sorted(QUAD_IDS[tuple(block)] for block in image["canonical_blocks"])
            for image in images[name]
        ]
        require(
            len(old) == len({tuple(ids) for ids in old}) == old_count,
            "all distinct audited old images",
        )
        require(all(len(ids) == len(set(ids)) == 20 for ids in old), "old image cardinality")
        model = cp_model.CpModel()
        variables = [model.new_bool_var(f"quad_{index}") for index in range(1365)]
        for pair in PAIRS:
            model.add(sum(variables[index] for index in pair_support[pair]) == 1 + (pair in excess))
        model.add(sum(variables) == 20)
        for triple in TRIPLES:
            model.add(sum(variables[index] for index in triple_support[triple]) <= 1)
        for ids in old:
            model.add(sum(variables[index] for index in ids) <= 19)
        require(
            len(model.proto.variables) == 1365 and len(model.proto.constraints) == 561 + old_count,
            "exact local model shape",
        )
        require(not model.validate(), "model validates")
        for old_index in (0, len(old) - 1):
            chosen = set(old[old_index])
            values = [int(index in chosen) for index in range(1365)]
            failed = violations(model, values)
            require(failed == [561 + old_index], "old image fails exactly its own nogood")
            controls.append(
                {
                    "case": number,
                    "old_image_index": old_index,
                    "violated_rows": failed,
                    "expected_nogood_row": 561 + old_index,
                }
            )
        fiber = next(row for row in fibers if row["class"] == name)
        profile = profiles[fiber["profile_ids"][0]]
        data = {
            "class": name,
            "canonical_excess_edges": sorted(excess),
            "old_image_quad_ids": old,
            "actual_point": 1,
            "actual_excess_link_id": fiber["excess_link_id"],
            "canonical_to_actual": fiber["canonical_to_actual"],
            "profile_id": profile["profile_id"],
            "profile_choice_mask": profile["choice_mask"],
            "profile_excess_triples": profile["excess_triples"],
            "profile_canonical_sha256": profile["canonical_sha256"],
        }
        case_dir = RAW / f"case-{number}"
        case_dir.mkdir()
        model_path, parameter_path = case_dir / "model.pbtxt", case_dir / "parameters.pbtxt"
        model_path.write_text(str(model.proto))
        parameter_path.write_text(str(parameters(seed)))
        data_path = HERE / f"case-{number}-data.json"
        dump(data_path, data)
        prepared.extend([model_path, parameter_path, data_path])
        cases.append(
            {
                "case": number,
                "class": name,
                "seed": seed,
                "seconds": SECONDS,
                "workers": WORKERS,
                "watchdog_seconds": 35.0,
                "grace_seconds": 5.0,
                "variables": 1365,
                "rows": 561 + old_count,
                "pair_rows": 105,
                "cardinality_rows": 1,
                "triple_cap_rows": 455,
                "old_image_nogoods": old_count,
                "model": str(model_path.relative_to(ROOT)),
                "parameters": str(parameter_path.relative_to(ROOT)),
                "data": str(data_path.relative_to(ROOT)),
            }
        )
    dump(
        HERE / "old-image-controls.json",
        {"passed": True, "controls": controls, "optimizer_calls": 0},
    )
    prepared.append(HERE / "old-image-controls.json")
    dependencies = [
        BASE,
        CLASSES,
        CATALOG_AUDIT,
        CATALOG / "canonical-images.json",
        CATALOG / "link-fibers.json",
        CATALOG / "profiles.json",
        CATALOG / "files.json",
        ROOT / "src/covering64/core.py",
        ROOT / "scripts/check_cover.py",
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
            "dependencies": {str(path.relative_to(ROOT)): sha(path) for path in dependencies},
            "prepared_files": {str(path.relative_to(ROOT)): sha(path) for path in prepared},
            "cases": cases,
            "max_calls": 4,
            "total_solver_seconds": 120,
            "watchdog_source": str(BASE.relative_to(ROOT)),
            "watchdog_source_sha256": BASE_SHA,
            "no_retry_or_budget_transfer": True,
            "objective": None,
            "hints": None,
            "optimizer_calls_during_preparation": 0,
            "scope": (
                "Restricted local witness searches beyond the audited images "
                "of four specific old witnesses. No completeness or global exclusion claim. "
                "Every found local witness is mapped and checked "
                "as an actual twenty-pentad partial before that terminology is used."
            ),
        },
    )
    print(
        json.dumps(
            {"prepared": True, "manifest_sha256": sha(HERE / "manifest.json"), "optimizer_calls": 0}
        )
    )


def pins():
    manifest = json.loads((HERE / "manifest.json").read_text())
    require(sha(__file__) == manifest["source_sha256"], "frozen runner")
    require(ortools.__version__ == manifest["ortools_version"], "solver version")
    for section in ("dependencies", "prepared_files"):
        for path, expected in manifest[section].items():
            require(sha(ROOT / path) == expected, "frozen dependency")
    require(len(manifest["cases"]) == 4, "four cases")
    for case, name, seed, count in zip(manifest["cases"], NAMES, SEEDS, OLD_COUNTS):
        require(
            (case["class"], case["seed"], case["old_image_nogoods"]) == (name, seed, count),
            "case bindings",
        )
        require(
            (case["seconds"], case["workers"], case["watchdog_seconds"], case["grace_seconds"])
            == (30, 1, 35, 5),
            "fixed budgets",
        )
    return manifest


def verify_new(blocks, data, destination):
    require(
        len(blocks) == len(set(blocks)) == 20 and blocks == sorted(blocks),
        "twenty distinct local blocks",
    )
    require(
        all(
            len(block) == 4
            and len(set(block)) == 4
            and all(type(x) is int and 1 <= x <= 15 for x in block)
            for block in blocks
        ),
        "strict local labels",
    )
    excess = {tuple(edge) for edge in data["canonical_excess_edges"]}
    pair_counts = Counter(pair for block in blocks for pair in combinations(block, 2))
    triple_counts = Counter(triple for block in blocks for triple in combinations(block, 3))
    require(
        all(pair_counts[pair] == 1 + (pair in excess) for pair in PAIRS), "all local pair demands"
    )
    require(len(triple_counts) == 80 and max(triple_counts.values()) == 1, "all local triple caps")
    chosen = {QUAD_IDS[block] for block in blocks}
    require(
        all(len(chosen.intersection(old)) <= 19 for old in data["old_image_quad_ids"]),
        "every old image excluded",
    )
    local_package, local_standalone = dual(blocks, 15, 4, 2)
    require(local_package["valid"] and local_standalone["valid"], "dual local pair cover checks")
    actual = sorted(
        tuple(sorted((data["actual_point"], *(data["canonical_to_actual"][x - 1] for x in block))))
        for block in blocks
    )
    actual_package, actual_standalone = dual(actual, 16, 5, 3)
    require(
        actual_package["covered"] == actual_standalone["covered_subsets"] == 185,
        "actual partial coverage",
    )
    require(
        len(actual_package["uncovered"]) == actual_standalone["uncovered_count"] == 375,
        "actual partial holes",
    )
    profile = {tuple(row) for row in data["profile_excess_triples"]}
    require(
        sha256(text_bytes(profile)).hexdigest() == data["profile_canonical_sha256"],
        "actual profile pin",
    )
    actual_counts = Counter(triple for block in actual for triple in combinations(block, 3))
    residual = {
        triple: 1 + (triple in profile) - actual_counts[triple]
        for triple in combinations(range(1, 17), 3)
    }
    require(
        min(residual.values()) >= 0 and sum(residual.values()) == 440, "actual nonnegative residual"
    )
    require(
        all(value == 0 for triple, value in residual.items() if data["actual_point"] in triple),
        "all actual point rows satisfied",
    )
    (destination / "canonical-k4.txt").write_bytes(text_bytes(blocks))
    (destination / "actual-partial.txt").write_bytes(text_bytes(actual))
    dump(destination / "local-package-verifier.json", local_package)
    dump(destination / "local-standalone-verifier.json", local_standalone)
    dump(destination / "actual-package-verifier.json", actual_package)
    dump(destination / "actual-standalone-verifier.json", actual_standalone)
    result = {
        "canonical_k4_sha256": sha(destination / "canonical-k4.txt"),
        "actual_partial_sha256": sha(destination / "actual-partial.txt"),
        "all_exact_pair_rows": True,
        "all_triple_caps": True,
        "all_old_nogoods": True,
        "actual_point": data["actual_point"],
        "profile_id": data["profile_id"],
        "profile_choice_mask": data["profile_choice_mask"],
        "actual_covered": 185,
        "actual_holes": 375,
        "remaining_demand_sum": 440,
        "global_cover": False,
    }
    dump(destination / "witness-check.json", result)
    return result


def worker(number):
    manifest = pins()
    require((HERE / "launch.json").exists() and 1 <= number <= 4, "root wrapper launch")
    case = manifest["cases"][number - 1]
    destination = HERE / f"case-{number}-output"
    destination.mkdir(exist_ok=False)
    model = cp_model.CpModel()
    require(
        model.proto.parse_text_format((ROOT / case["model"]).read_text()) and not model.validate(),
        "frozen valid model",
    )
    solver = cp_model.CpSolver()
    require(
        solver.parameters.parse_text_format((ROOT / case["parameters"]).read_text()),
        "frozen parameters",
    )
    require(str(solver.parameters) == str(parameters(case["seed"])), "exact parameters")
    status = solver.solve(model)
    result = {
        "case": number,
        "class": case["class"],
        "seed": case["seed"],
        "status": solver.status_name(status),
        "wall_time_seconds": solver.wall_time,
        "branches": solver.num_branches,
        "conflicts": solver.num_conflicts,
        "response_stats": solver.response_stats(),
        "manifest_sha256": sha(HERE / "manifest.json"),
        "model_sha256": sha(ROOT / case["model"]),
        "parameters_sha256": sha(ROOT / case["parameters"]),
        "source_revision": manifest["source_revision"],
        "ortools_version": ortools.__version__,
        "proof_generated": False,
        "witness": None,
        "scope": "One specified local excess graph beyond the listed old witness images only.",
        "status_note": (
            "UNKNOWN is inconclusive; INFEASIBLE is not an independently checked theorem."
        ),
    }
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        values = [solver.value(model.get_bool_var_from_proto_index(index)) for index in range(1365)]
        require(
            set(values) <= {0, 1} and sum(values) == 20 and not violations(model, values),
            "exact model vector",
        )
        blocks = [block for block, value in zip(QUADS, values) if value]
        result["witness"] = verify_new(
            blocks, json.loads((ROOT / case["data"]).read_text()), destination
        )
        dump(destination / "values.json", values)
    dump(destination / "result.json", result)


def run():
    manifest = pins()
    require(not any(HERE.glob("case-*-output")), "fresh outputs")
    descriptor = os.open(HERE / "launch.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        json.dump({"manifest_sha256": sha(HERE / "manifest.json"), "max_calls": 4}, handle)
        handle.write("\n")
    runner = module(BASE, "frozen_watchdog_runner")
    require(runner.WATCHDOG == 35 and runner.GRACE == 5, "frozen watchdog limits")
    receipts = []
    for case in manifest["cases"]:
        pins()
        number = case["case"]
        stdout_path, stderr_path = (
            HERE / f"case-{number}-stdout.log",
            HERE / f"case-{number}-stderr.log",
        )
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            receipt = runner.bounded_child(
                [sys.executable, str(Path(__file__).resolve()), "_worker", str(number)],
                stdout,
                stderr,
            )
        result_path = HERE / f"case-{number}-output/result.json"
        receipt.update(
            {
                "case": number,
                "stdout_sha256": sha(stdout_path),
                "stderr_sha256": sha(stderr_path),
                "result_sha256": sha(result_path) if result_path.exists() else None,
            }
        )
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
        raise SystemExit("Usage: run.py prepare|run|_worker CASE")
