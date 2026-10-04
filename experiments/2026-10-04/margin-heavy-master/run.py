# Document:    Bounded Maximum-Margin Heavy Master Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      37f6152e195aafe2794699ba11096db2e15c0aff647ae2a746bf9cd9b4d32ad8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Maximize the minimum normalized margin inside all checked completion cuts."""

import argparse
import importlib.util
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from ortools import __version__ as ortools_version
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
RAW = ROOT / "experiments/scratch/margin-heavy-master-20261004"
NEAREST = DAY / "nearest-heavy-master"
NEAREST_RAW = ROOT / "experiments/scratch/nearest-heavy-master-20261004"
SEED = 2026104064
SCALE = 1000000


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


helpers = load(NEAREST / "run.py", "frozen_nearest_helpers")
sha, dump = helpers.sha, helpers.dump


def load_cuts():
    base, cuts, paths = helpers.load_cuts()
    prior_path = NEAREST / "result.json"
    prior = json.loads(prior_path.read_text())
    gate_path = DAY / "nearest-heavy-master-independent/postcheck.json"
    gate = json.loads(gate_path.read_text())
    assert gate["passed"]
    assert prior["new_cuts"] == len(prior["records"]) == 95
    paths += [prior_path, gate_path, NEAREST / "run.py", NEAREST / "manifest.json"]
    for record in prior["records"]:
        path = NEAREST_RAW / f"step-{record['step']:03d}/learned-cut.json"
        assert sha(path) == record["learned_cut_sha256"]
        paths.append(path)
        cuts.append(json.loads(path.read_text()))
    assert len(cuts) == 333
    return base, cuts, paths


def normalized(cuts):
    planes = []
    for cut in cuts:
        denominator = cut["denominator"]
        assert SCALE % denominator == 0
        factor = SCALE // denominator
        planes.append(([factor * c for c in cut["coefficients"]], factor * cut["rhs"]))
    assert all(len(coefficients) == 276 for coefficients, _ in planes)
    upper = min(sum(sorted(coefficients, reverse=True)[:28]) - rhs for coefficients, rhs in planes)
    assert 0 <= upper < 2**60
    assert all(
        abs(rhs) + sum(abs(c) for c in coefficients) + upper < 2**60 for coefficients, rhs in planes
    )
    return planes, upper


def build(original, heavy, global_ids, cuts):
    model, variables = original.build_master(heavy, global_ids, [])
    planes, upper = normalized(cuts)
    margin = model.new_int_var(0, upper, "minimum_cut_margin_units")
    for coefficients, rhs in planes:
        model.add(sum(c * x for c, x in zip(coefficients, variables, strict=True)) - margin >= rhs)
    model.maximize(margin)
    return model, variables, margin, upper


def prepare():
    assert not RAW.exists() and not (HERE / "manifest.json").exists()
    original, sweep = helpers.sources()
    base, cuts, paths = load_cuts()
    blocks, ordinary, heavy, _, rows = sweep.basis()
    assert base["heavy_global_ids"] == [blocks.index(block) for block in heavy]
    assert base["ordinary_global_ids"] == [blocks.index(block) for block in ordinary]
    model, _, _, upper = build(original, heavy, base["heavy_global_ids"], cuts)
    assert model.validate() == "" and upper == 141507155
    proto_bytes = str(model.proto).encode()
    RAW.mkdir()
    (RAW / "master.pbtxt").write_bytes(proto_bytes)
    (RAW / "run-frozen.py").write_bytes(Path(__file__).read_bytes())
    previous_manifest = json.loads((NEAREST / "manifest.json").read_text())
    inputs = {str(path.relative_to(ROOT)): sha(path) for path in paths}
    inputs.update(previous_manifest["input_files"])
    manifest = {
        "source_sha256": sha(__file__),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "input_files": inputs,
        "master_sha256": sha(RAW / "master.pbtxt"),
        "master_variables": len(model.proto.variables),
        "master_rows": len(model.proto.constraints),
        "cut_count": len(cuts),
        "completion_rows": len(rows),
        "ordinary_columns": len(ordinary),
        "common_denominator": SCALE,
        "safe_margin_upper_units": upper,
        "baseline_heavy_global_ids": previous_manifest["baseline_heavy_global_ids"],
        "baseline_elastic_objective": previous_manifest["baseline_elastic_objective"],
        "budget": {
            "candidates": 20,
            "master_seconds_each": 3,
            "lp_seconds_each": 1,
            "combined_solver_seconds": 80,
            "wall_seconds": 100,
            "workers": 1,
            "seed": SEED,
        },
        "optimizer_calls": 0,
    }
    dump(HERE / "manifest.json", manifest)
    print(json.dumps({key: value for key, value in manifest.items() if key != "input_files"}))


def run(gate_path):
    started = time.monotonic()
    manifest = json.loads((HERE / "manifest.json").read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] and gate["manifest_sha256"] == sha(HERE / "manifest.json")
    assert gate["source_sha256"] == sha(__file__) == manifest["source_sha256"]
    assert not (RAW / "start.json").exists() and not (HERE / "result.json").exists()
    for relative, expected in manifest["input_files"].items():
        assert sha(ROOT / relative) == expected
    original, sweep = helpers.sources()
    base, cuts, _ = load_cuts()
    blocks, ordinary, heavy, _, rows = sweep.basis()
    lp = helpers.load(sweep.generator.LP_CORE, "margin_exact_lp")
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
    solver_seconds = 0.0
    best_objective = manifest["baseline_elastic_objective"]
    best_ids = manifest["baseline_heavy_global_ids"]
    stop_reason = "candidate_limit"
    for step in range(20):
        if solver_seconds >= 75.8 or time.monotonic() - started >= 94:
            stop_reason = "solver_or_wall_budget"
            break
        directory = RAW / f"step-{step:03d}"
        directory.mkdir()
        model, variables, margin, upper = build(original, heavy, base["heavy_global_ids"], cuts)
        (directory / "master.pbtxt").write_text(str(model.proto))
        if step == 0:
            assert sha(directory / "master.pbtxt") == manifest["master_sha256"]
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 3
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
        solver_seconds += master_seconds
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
            "master_sha256": sha(directory / "master.pbtxt"),
            "safe_margin_upper_units": upper,
        }
        records.append(record)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            stop_reason = "master_without_candidate"
            break
        fixed = {index for index, variable in enumerate(variables) if solver.value(variable)}
        assert len(fixed) == 28
        heavy_ids = [base["heavy_global_ids"][index] for index in sorted(fixed)]
        margin_value = solver.value(margin)
        planes, _ = normalized(cuts)
        actual_minimum = min(
            sum(coefficients[index] for index in fixed) - rhs for coefficients, rhs in planes
        )
        assert 0 <= margin_value <= actual_minimum and solver.objective_value == margin_value
        record.update(
            heavy_global_ids=heavy_ids,
            margin_units=margin_value,
            actual_minimum_margin_units=actual_minimum,
            margin_bound_units=solver.best_objective_bound,
        )
        family = [heavy[index] for index in sorted(fixed)]
        shifted = sweep.generator.shifted_rows(rows, heavy, family)
        dump(directory / "completion-rows.json", shifted)
        numerical, values, dual = sweep.solve(shifted)
        solver_seconds += numerical["seconds"]
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
        cut = helpers.derive_cut(lp, rows, shifted, dual, fixed, len(ordinary), len(heavy))
        if cut is None:
            stop_reason = "unresolved_exact_dual"
            break
        assert max(abs(weight) for _, weight in cut["dual"]["weights"]) <= SCALE
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
                    "master_status": record["master_status"],
                    "margin_units": margin_value,
                    "elastic_objective": numerical["objective"],
                    "best": best_objective,
                    "combined_solver_seconds": solver_seconds,
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
        "combined_solver_seconds": solver_seconds,
        "wall_seconds": elapsed,
        "records": records,
        "stop_reason": stop_reason,
        "exact_fractional_feasibility": stop_reason == "exact_fractional_feasibility",
        "covering_witness": False,
        "global_lower_bound_claim": False,
    }
    assert solver_seconds <= 80 and elapsed <= 100
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
