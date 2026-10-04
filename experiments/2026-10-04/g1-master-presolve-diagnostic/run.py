# Document:    Fixed-g1 Identical-Model Presolve Diagnostic
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      836b906eb76394721ce53ecb2b0e0c0e94207b0d1d76452db92819aff51a85be
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Compare two bounded parameter settings without changing the initial model."""

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
PRIOR = DAY / "g1-nearest-master"
PREP = ROOT / "experiments/scratch/g1-master-presolve-diagnostic-preparation-20261004"
RAW = ROOT / "experiments/scratch/g1-master-presolve-diagnostic-20261004"
CASES = [("normal-presolve", True), ("presolve-off", False)]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


master = load(PRIOR / "run.py", "presolve_frozen_master")
branch = master.branch
sha = master.sha
data_hash = master.data_hash


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def solver_for(presolve):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = master.SEED
    solver.parameters.randomize_search = True
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    solver.parameters.cp_model_presolve = presolve
    return solver


def rebuild():
    prior = json.loads((PRIOR / "manifest.json").read_text())
    broad, conditional, _, _ = master.inputs()
    blocks, ordinary, heavy, _, rows, _ = branch.basis()
    registry = branch.registry_module.Registry()
    nogoods = master.initial_nogoods(blocks, prior["heavy_global_ids"], registry)
    model, variables = master.build(
        heavy,
        prior["heavy_global_ids"],
        broad + conditional,
        nogoods,
        prior["baseline_heavy_global_ids"],
    )
    assert sha(ROOT / prior["master_path"]) == prior["master_sha256"]
    assert str(model.proto) == (ROOT / prior["master_path"]).read_text()
    return (
        prior,
        blocks,
        ordinary,
        heavy,
        rows,
        registry,
        model,
        variables,
        broad + conditional,
        nogoods,
    )


def prepare():
    assert not PREP.exists() and not (HERE / "manifest.json").exists()
    prior, _, _, _, _, _, model, _, _, _ = rebuild()
    old = json.loads((PRIOR / "result.json").read_text())
    assert len(old["records"]) == 1 and old["records"][0]["master_status"] == "UNKNOWN"
    post_path = DAY / "g1-nearest-master-independent/postcheck.json"
    assert json.loads(post_path.read_text())["passed"]
    PREP.mkdir()
    (PREP / "master.pbtxt").write_text(str(model.proto))
    cases = []
    for name, presolve in CASES:
        solver = solver_for(presolve)
        path = PREP / f"{name}-parameters.pbtxt"
        path.write_text(str(solver.parameters))
        cases.append(
            {
                "name": name,
                "cp_model_presolve": presolve,
                "parameters_path": str(path.relative_to(ROOT)),
                "parameters_sha256": sha(path),
                "master_seconds": 10,
                "worker_count": 1,
                "seed": master.SEED,
                "completion_lp_seconds": 1,
            }
        )
    inputs = prior["input_files"].copy()
    paths = [
        Path(__file__),
        PRIOR / "run.py",
        PRIOR / "manifest.json",
        PRIOR / "result.json",
        DAY / "g1-nearest-master-independent/audit.json",
        post_path,
    ]
    inputs.update({str(path.relative_to(ROOT)): sha(path) for path in paths})
    for relative, digest in inputs.items():
        assert sha(ROOT / relative) == digest
    manifest = {
        "source_sha256": sha(__file__),
        "source_revision_at_freeze": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "input_files": inputs,
        "graph_index": 1,
        "family_sha256": prior["family_sha256"],
        "model_sha256": sha(PREP / "master.pbtxt"),
        "original_model_sha256": prior["master_sha256"],
        "model_path": str((PREP / "master.pbtxt").relative_to(ROOT)),
        "cases": cases,
        "baseline_elastic_objective": prior["baseline_elastic_objective"],
        "baseline_heavy_global_ids": prior["baseline_heavy_global_ids"],
        "heavy_global_ids": prior["heavy_global_ids"],
        "ordinary_global_ids": prior["ordinary_global_ids"],
        "optimization_calls": 0,
        "budgets": {
            "master_calls": 2,
            "seconds_per_master": 10,
            "lp_calls_per_distinct_accepted_tuple": 1,
            "seconds_per_lp": 1,
            "maximum_lp_calls": 2,
            "workers": 1,
            "master_seed": master.SEED,
            "lp_seed": 2026104,
        },
        "stop_policy": (
            "On numerical LP zero, attempt exact rational primal verification "
            "and stop the diagnostic."
        ),
        "scope": (
            "Identical initial fixed-g1 model; only time limit and explicit presolve "
            "Boolean differ from the prior run."
        ),
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "source_sha256": sha(__file__),
                "model_sha256": manifest["model_sha256"],
                "cases": cases,
                "optimization_calls": 0,
            }
        )
    )


def run(gate_path):
    manifest = json.loads((HERE / "manifest.json").read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] and gate["manifest_sha256"] == sha(HERE / "manifest.json")
    assert gate["source_sha256"] == sha(__file__) == manifest["source_sha256"]
    for relative, digest in manifest["input_files"].items():
        assert sha(ROOT / relative) == digest
    assert not RAW.exists() and not (HERE / "result.json").exists()
    RAW.mkdir()
    for path in [Path(__file__), HERE / "manifest.json", gate_path]:
        (RAW / path.name).write_bytes(path.read_bytes())
    started = time.monotonic()
    prior, blocks, ordinary, heavy, rows, registry, model, variables, cuts, nogoods = rebuild()
    exact = master.load(branch.generator.LP_CORE, "presolve_exact")
    start = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": sha(__file__),
        "manifest_sha256": sha(HERE / "manifest.json"),
        "gate_sha256": sha(gate_path),
        "ortools_version": ortools_version,
        "graph_index": 1,
        "family_sha256": manifest["family_sha256"],
        "budgets": manifest["budgets"],
    }
    dump(RAW / "start.json", start)
    results = []
    evaluated = {}
    lp_calls = 0
    total_solver = 0.0
    best_objective = manifest["baseline_elastic_objective"]
    best_ids = manifest["baseline_heavy_global_ids"]
    improvements = []
    numerical_zero = False
    exact_feasible = False
    for case in manifest["cases"]:
        name = case["name"]
        folder = RAW / name
        folder.mkdir()
        path = folder / "master.pbtxt"
        path.write_text(str(model.proto))
        assert sha(path) == manifest["model_sha256"] == manifest["original_model_sha256"]
        solver = solver_for(case["cp_model_presolve"])
        (folder / "parameters.pbtxt").write_text(str(solver.parameters))
        assert sha(folder / "parameters.pbtxt") == case["parameters_sha256"]
        logs = []
        solver.log_callback = logs.append
        before = time.monotonic()
        status = solver.solve(model)
        elapsed = time.monotonic() - before
        total_solver += elapsed
        (folder / "solver.log").write_text("".join(logs))
        (folder / "response.pbtxt").write_text(str(solver.response_proto))
        assert str(model.proto) == path.read_text()
        record = {
            "name": name,
            "cp_model_presolve": case["cp_model_presolve"],
            "master_status": solver.status_name(status),
            "master_seconds": elapsed,
            "master_reported_seconds": solver.wall_time,
            "model_sha256": sha(path),
            "parameters_sha256": sha(folder / "parameters.pbtxt"),
            "response_sha256": sha(folder / "response.pbtxt"),
            "log_sha256": sha(folder / "solver.log"),
            "lp_called": False,
        }
        results.append(record)
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            positions = {i for i, variable in enumerate(variables) if solver.value(variable)}
            assert len(positions) == 28
            ids = [prior["heavy_global_ids"][i] for i in sorted(positions)]
            assert all(sum(cut["coefficients"][i] for i in positions) >= cut["rhs"] for cut in cuts)
            assert all(
                sum(i in positions for i in item["heavy_local_ids"]) <= 6 for item in nogoods
            )
            distance = 28 - len(set(ids) & set(manifest["baseline_heavy_global_ids"]))
            assert solver.objective_value == distance
            fixed = [heavy[i] for i in sorted(positions)]
            receipt = registry.classify(fixed)
            dump(folder / "registry.json", receipt)
            record.update(
                heavy_global_ids=ids,
                heavy_sha256=data_hash(fixed),
                distance_replacements=distance,
                objective_bound=solver.best_objective_bound,
                registry_accepted=receipt["accepted"],
                registry_sha256=sha(folder / "registry.json"),
                rejected_links=[
                    {
                        "anchor_group_zero_based": link["anchor_group_zero_based"],
                        "representative": link["representative"],
                        "proof_sources": link["proof_sources"],
                    }
                    for link in receipt["links"]
                    if link["excluded"]
                ],
            )
            if receipt["accepted"]:
                key = tuple(ids)
                shifted = branch.generator.shifted_rows(rows, heavy, fixed)
                record["shifted_rows_sha256"] = data_hash(shifted)
                if key in evaluated:
                    prior_record = evaluated[key]
                    assert record["shifted_rows_sha256"] == prior_record["shifted_rows_sha256"]
                    record.update(
                        lp_reused=True,
                        reused_case=prior_record["name"],
                        reused_lp_record_sha256=data_hash(prior_record),
                        lp=prior_record["lp"],
                    )
                else:
                    dump(folder / "completion-rows.json", shifted)
                    numerical, values, dual = branch.sweep.solve(shifted)
                    total_solver += numerical["seconds"]
                    lp_calls += 1
                    record.update(lp_called=True, lp=numerical)
                    if values is not None:
                        dump(folder / "primal.json", values)
                        dump(folder / "dual.json", dual)
                        record.update(
                            vector_path=str((folder / "primal.json").relative_to(ROOT)),
                            vector_sha256=sha(folder / "primal.json"),
                            dual_path=str((folder / "dual.json").relative_to(ROOT)),
                            dual_sha256=sha(folder / "dual.json"),
                        )
                        if (
                            numerical["status"] == "OPTIMAL"
                            and numerical["objective"] < best_objective - 1e-7
                        ):
                            best_objective = numerical["objective"]
                            best_ids = ids
                            improvements.append(
                                {
                                    "status": "OPTIMAL",
                                    "objective": best_objective,
                                    "rank": len(results) - 1,
                                    "heavy_global_ids": ids,
                                    "heavy_sha256": record["heavy_sha256"],
                                }
                            )
                        if numerical["recomputed_l1_residual"] <= 1e-7:
                            numerical_zero = True
                            attempts = []
                            for limit in (100, 10000, 1000000, 1000000000):
                                primal = exact.exact_primal(shifted, values, limit)
                                attempts.append(
                                    {"denominator_limit": limit, "passed": primal is not None}
                                )
                                if primal is not None:
                                    primal.update(
                                        graph_index=1,
                                        family_sha256=manifest["family_sha256"],
                                        heavy_global_ids=ids,
                                        ordinary_global_ids=manifest["ordinary_global_ids"],
                                        shifted_rows_sha256=record["shifted_rows_sha256"],
                                    )
                                    dump(HERE / "exact-primal.json", primal)
                                    exact_feasible = True
                                    break
                            dump(folder / "exact-primal-attempts.json", attempts)
                    evaluated[key] = record.copy()
        dump(RAW / "cases.json", results)
        print(json.dumps(record), flush=True)
        if numerical_zero:
            break
    assert len(results) <= 2 and lp_calls <= len(evaluated) <= 2
    result = {
        **start,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "master_calls": len(results),
        "fresh_completion_lps": lp_calls,
        "solver_seconds": total_solver,
        "wall_seconds": time.monotonic() - started,
        "initial_objective": manifest["baseline_elastic_objective"],
        "best_objective": best_objective,
        "best_heavy_global_ids": best_ids,
        "cases": results,
        "improvements": improvements,
        "numerical_zero": numerical_zero,
        "exact_fractional_feasibility": exact_feasible,
        "covering_witness": False,
        "global_lower_bound_claim": False,
        "complete_diagnostic": len(results) == 2,
        "stop_reason": "numerical_zero" if numerical_zero else "two_parameter_cases_completed",
    }
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
            {
                key: value
                for key, value in result.items()
                if key not in ("cases", "improvements", "raw_sha256")
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "run"])
    parser.add_argument("--gate", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        assert args.gate is not None
        run(args.gate)
