# Document:    Bounded Nearest-Heavy Lazy Master with Exact Completion Cuts
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      bbe2edc3da54e6b4f612e30d5303ae093e1d03d6cd074193ef723cfe3a2943d4
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prefer nearby heavy tuples using a soft Hamming objective and checked cuts."""

import argparse
import hashlib
import importlib.util
import json
import math
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from ortools import __version__ as ortools_version
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
OLD = ROOT / "experiments/2026-10-03"
RAW = ROOT / "experiments/scratch/nearest-heavy-master-20261004"
SEED = 2026104063


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sources():
    original = load(DAY / "lazy-heavy-master/run.py", "nearest_original_master")
    sweep = load(DAY / "lp-guided-full-sweep/sweep.py", "nearest_frozen_sweep")
    return original, sweep


def load_cuts():
    paths = [OLD / "cut-survivor-lp-screen/cut-bundle.json"]
    base = json.loads(paths[0].read_text())
    base_gate_path = DAY / "cut-bundle-independent/audit.json"
    base_gate = json.loads(base_gate_path.read_text())
    assert base_gate["passed"] and base_gate["bundle_sha256"] == sha(paths[0])
    paths.append(base_gate_path)
    cuts = list(base["cuts"])
    assert len(cuts) == 14
    for folder, expected, pattern in (
        ("lazy-heavy-master-independent", 10, "learned-cut-"),
        ("lazy-heavy-master-continuation", 100, "/learned-cut.json"),
    ):
        gate_path = DAY / folder / "postcheck.json"
        gate = json.loads(gate_path.read_text())
        assert gate["passed"] and gate["checked_new_cuts"] == expected
        matched = [
            (ROOT / path, value) for path, value in gate["receipts"].items() if pattern in path
        ]
        assert len(matched) == expected
        paths.append(gate_path)
        for path, expected_hash in sorted(matched):
            assert sha(path) == expected_hash
            paths.append(path)
            cuts.append(json.loads(path.read_text()))
    assert len(cuts) == 124
    sweep_path = DAY / "lp-guided-sweep-cuts/bundle.json"
    sweep = json.loads(sweep_path.read_text())
    assert len(sweep["cuts"]) == 113
    assert sweep["heavy_global_ids"] == base["heavy_global_ids"]
    assert sweep["ordinary_global_ids"] == base["ordinary_global_ids"]
    paths.append(sweep_path)
    for cut in sweep["cuts"]:
        path = ROOT / cut["certificate_path"]
        assert sha(path) == cut["certificate_sha256"]
        paths.append(path)
        cuts.append(cut)
    best_path = DAY / "lp-guided-best-lp/cut.json"
    best = json.loads(best_path.read_text())
    assert best["heavy_global_ids"] == base["heavy_global_ids"]
    assert best["ordinary_global_ids"] == base["ordinary_global_ids"]
    dual_path = ROOT / best["dual_path"]
    assert sha(dual_path) == best["dual_sha256"]
    paths += [best_path, dual_path]
    cuts.append(best)
    assert len(cuts) == 238 and all(len(cut["coefficients"]) == 276 for cut in cuts)
    return base, cuts, paths


def objective_master(original, heavy, global_ids, cuts, baseline_ids):
    model, variables = original.build_master(heavy, global_ids, cuts)
    lookup = {global_id: local_id for local_id, global_id in enumerate(global_ids)}
    assert len(baseline_ids) == len(set(baseline_ids)) == 28
    model.minimize(28 - sum(variables[lookup[global_id]] for global_id in baseline_ids))
    return model, variables


def prepare():
    assert not RAW.exists() and not (HERE / "manifest.json").exists()
    original, sweep = sources()
    base, cuts, paths = load_cuts()
    blocks, ordinary, heavy, _, rows = sweep.basis()
    baseline_path = DAY / "lp-guided-full-sweep/result.json"
    baseline = json.loads(baseline_path.read_text())
    baseline_ids = baseline["best_heavy_global_ids"]
    assert baseline["complete_neighborhood"] and baseline["best_objective"] == 5.575882992498541
    assert base["heavy_global_ids"] == [blocks.index(block) for block in heavy]
    assert base["ordinary_global_ids"] == [blocks.index(block) for block in ordinary]
    model, _ = objective_master(original, heavy, base["heavy_global_ids"], cuts, baseline_ids)
    assert model.validate() == ""
    model_bytes = str(model.proto).encode()
    normalized = []
    for cut in cuts:
        divisor = math.gcd(*cut["coefficients"], cut["rhs"])
        normalized.append(tuple(value // divisor for value in [*cut["coefficients"], cut["rhs"]]))
    RAW.mkdir()
    (RAW / "master.pbtxt").write_bytes(model_bytes)
    (RAW / "run-frozen.py").write_bytes(Path(__file__).read_bytes())
    paths += [
        DAY / "lazy-heavy-master/run.py",
        DAY / "lp-guided-full-sweep/sweep.py",
        DAY / "lp-guided-link-switch/prepare.py",
        sweep.generator.SOURCE,
        sweep.generator.LP_CORE,
        sweep.generator.MANIFEST,
        sweep.generator.SEED,
        ROOT / json.loads(sweep.generator.MANIFEST.read_text())["model"],
        baseline_path,
    ]
    manifest = {
        "source_sha256": sha(__file__),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "input_files": {str(path.relative_to(ROOT)): sha(path) for path in paths},
        "master_sha256": hashlib.sha256(model_bytes).hexdigest(),
        "master_variables": len(model.proto.variables),
        "master_rows": len(model.proto.constraints),
        "completion_rows": len(rows),
        "ordinary_columns": len(ordinary),
        "heavy_columns": len(heavy),
        "cut_count": len(cuts),
        "unique_normalized_cuts": len(set(normalized)),
        "exact_scaled_duplicates": len(cuts) - len(set(normalized)),
        "baseline_heavy_global_ids": baseline_ids,
        "baseline_elastic_objective": baseline["best_objective"],
        "objective": "28 minus baseline heavy blocks selected; half full binary Hamming distance.",
        "budget": {
            "candidates": 100,
            "master_seconds_each": 2,
            "lp_seconds_each": 1,
            "combined_solver_seconds": 180,
            "wall_seconds": 240,
            "workers": 1,
            "seed": SEED,
        },
        "optimization_calls": 0,
    }
    dump(HERE / "manifest.json", manifest)
    print(json.dumps({key: value for key, value in manifest.items() if key != "input_files"}))


def derive_cut(lp, rows, shifted, numerical_dual, fixed, ordinary_count, heavy_count):
    certificate = lp.exact_dual(shifted, numerical_dual, 1000000)
    if not certificate["proves_infeasible"]:
        return None
    ordinary, heavy, constant = [0] * ordinary_count, [0] * heavy_count, 0
    for row_index, weight in certificate["weights"]:
        ordinary_ids, heavy_ids, lower, upper = rows[row_index]
        bound = lower if weight > 0 else upper
        assert abs(bound) < 2**60
        constant += weight * bound
        for index in ordinary_ids:
            ordinary[index] += weight
        for index in heavy_ids:
            heavy[index] += weight
    box = sum(max(0, value) for value in ordinary)
    lhs = sum(heavy[index] for index in fixed)
    assert box == certificate["box_max_numerator"]
    assert constant - lhs == certificate["rhs_numerator"] and lhs < constant - box
    return {
        "coefficients": heavy,
        "rhs": constant - box,
        "denominator": 1000000,
        "constant": constant,
        "ordinary_box_max": box,
        "ordinary_coefficients": ordinary,
        "source_lhs": lhs,
        "dual": certificate,
    }


def run(gate_path):
    started = time.monotonic()
    manifest = json.loads((HERE / "manifest.json").read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] and gate["manifest_sha256"] == sha(HERE / "manifest.json")
    assert gate["source_sha256"] == sha(__file__) == manifest["source_sha256"]
    assert not (RAW / "start.json").exists() and not (HERE / "result.json").exists()
    for relative, expected in manifest["input_files"].items():
        assert sha(ROOT / relative) == expected
    original, sweep = sources()
    base, cuts, _ = load_cuts()
    blocks, ordinary, heavy, _, rows = sweep.basis()
    lp = load(sweep.generator.LP_CORE, "nearest_exact_lp")
    start = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": sha(__file__),
        "manifest_sha256": sha(HERE / "manifest.json"),
        "gate_sha256": sha(gate_path),
        "ortools_version": ortools_version,
        "budget": manifest["budget"],
    }
    dump(RAW / "start.json", start)
    (RAW / "gate.json").write_bytes(gate_path.read_bytes())
    records, improvements = [], []
    total_solver = 0.0
    best_objective = manifest["baseline_elastic_objective"]
    best_ids = manifest["baseline_heavy_global_ids"]
    stop_reason = "candidate_limit"
    for step in range(100):
        if total_solver >= 176.8 or time.monotonic() - started >= 234:
            stop_reason = "solver_or_wall_budget"
            break
        directory = RAW / f"step-{step:03d}"
        directory.mkdir()
        model, variables = objective_master(
            original, heavy, base["heavy_global_ids"], cuts, manifest["baseline_heavy_global_ids"]
        )
        proto_bytes = str(model.proto).encode()
        (directory / "master.pbtxt").write_bytes(proto_bytes)
        if step == 0:
            assert hashlib.sha256(proto_bytes).hexdigest() == manifest["master_sha256"]
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 2
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = SEED + step
        solver.parameters.randomize_search = True
        solver.parameters.log_search_progress = True
        solver.parameters.log_to_stdout = False
        logs = []
        solver.log_callback = logs.append
        before = time.monotonic()
        status = solver.solve(model)
        master_seconds = time.monotonic() - before
        total_solver += master_seconds
        (directory / "solver.log").write_text("".join(logs))
        (directory / "response.pbtxt").write_text(str(solver.response_proto))
        (directory / "parameters.pbtxt").write_text(str(solver.parameters))
        record = {
            "step": step,
            "master_status": solver.status_name(status),
            "master_seconds": master_seconds,
            "master_reported_seconds": solver.wall_time,
            "cut_count": len(cuts),
            "seed": SEED + step,
            "master_sha256": hashlib.sha256(proto_bytes).hexdigest(),
        }
        records.append(record)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            stop_reason = "master_without_candidate"
            break
        fixed = {i for i, variable in enumerate(variables) if solver.value(variable)}
        assert len(fixed) == 28
        heavy_ids = [base["heavy_global_ids"][index] for index in sorted(fixed)]
        distance = 28 - len(set(heavy_ids) & set(manifest["baseline_heavy_global_ids"]))
        assert solver.objective_value == distance
        assert all(sum(cut["coefficients"][index] for index in fixed) >= cut["rhs"] for cut in cuts)
        record.update(
            heavy_global_ids=heavy_ids,
            distance_replacements=distance,
            objective_bound=solver.best_objective_bound,
        )
        family = [heavy[index] for index in sorted(fixed)]
        shifted = sweep.generator.shifted_rows(rows, heavy, family)
        dump(directory / "completion-rows.json", shifted)
        numerical, values, dual = sweep.solve(shifted)
        total_solver += numerical["seconds"]
        record["lp"] = numerical
        if values is None:
            stop_reason = "lp_without_solution"
            break
        dump(directory / "numerical-primal.json", values)
        dump(directory / "numerical-dual.json", dual)
        record["heavy_sha256"] = sweep.generator.data_hash(family)
        if numerical["status"] == "OPTIMAL" and numerical["objective"] < best_objective - 1e-7:
            best_objective, best_ids = numerical["objective"], heavy_ids
            improvements.append(
                {
                    "status": "OPTIMAL",
                    "objective": best_objective,
                    "rank": step,
                    "heavy_global_ids": heavy_ids,
                    "heavy_sha256": record["heavy_sha256"],
                }
            )
        if numerical["recomputed_l1_residual"] <= 1e-7:
            primal = None
            for limit in (100, 10000, 1000000, 1000000000):
                primal = lp.exact_primal(shifted, values, limit)
                if primal is not None:
                    primal.update(
                        heavy_global_ids=heavy_ids, ordinary_global_ids=base["ordinary_global_ids"]
                    )
                    dump(HERE / "exact-primal.json", primal)
                    break
            stop_reason = (
                "exact_fractional_feasibility"
                if primal is not None
                else "unresolved_numerical_feasibility"
            )
            break
        cut = derive_cut(lp, rows, shifted, dual, fixed, len(ordinary), len(heavy))
        if cut is None:
            stop_reason = "unresolved_exact_dual"
            break
        dump(directory / "learned-cut.json", cut)
        record.update(
            gap=cut["dual"]["gap"], learned_cut_sha256=sha(directory / "learned-cut.json")
        )
        cuts.append(cut)
        dump(RAW / "steps.json", records)
        print(
            json.dumps(
                {
                    "step": step,
                    "distance": distance,
                    "master_status": record["master_status"],
                    "elastic_objective": numerical["objective"],
                    "best": best_objective,
                    "gap": record["gap"],
                    "total_solver_seconds": total_solver,
                }
            ),
            flush=True,
        )
    elapsed = time.monotonic() - started
    result = {
        **start,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "initial_objective": manifest["baseline_elastic_objective"],
        "best_objective": best_objective,
        "best_heavy_global_ids": best_ids,
        "initial_cuts": manifest["cut_count"],
        "new_cuts": len(cuts) - manifest["cut_count"],
        "combined_solver_seconds": total_solver,
        "wall_seconds": elapsed,
        "records": records,
        "stop_reason": stop_reason,
        "exact_fractional_feasibility": stop_reason == "exact_fractional_feasibility",
        "covering_witness": False,
        "global_lower_bound_claim": False,
    }
    assert total_solver <= 180 and elapsed <= 240
    result["raw_sha256"] = {
        str(path.relative_to(RAW)): sha(path) for path in sorted(RAW.rglob("*")) if path.is_file()
    }
    dump(HERE / "result.json", result)
    dump(
        HERE / "stitch-input.json",
        {"initial_objective": manifest["baseline_elastic_objective"], "records": improvements},
    )
    print(
        json.dumps(
            {key: value for key, value in result.items() if key not in ("records", "raw_sha256")}
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("gate", type=Path, nargs="?")
    args = parser.parse_args()
    prepare() if args.action == "prepare" else run(args.gate)
