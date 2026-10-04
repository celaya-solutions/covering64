# Document:    Bounded LP-Guided Link Switch Pilot
# Version:     v1.0.1
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      725bb19a966863fd77bd359f30ab09b3a7b14235b084821293f939747fdc84f9
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Run at most three reviewed rounds, sixty LPs and thirty solver seconds."""

import argparse
import importlib.util
import json
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import prepare
from ortools import __version__ as ortools_version
from ortools.linear_solver import pywraplp

HERE, ROOT = prepare.HERE, prepare.ROOT
RAW = ROOT / "experiments/scratch/lp-guided-link-switch-20261004"


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def solve(rows):
    """Same frozen elastic LP, with a one-second solve cap for the total budget."""
    solver = pywraplp.Solver.CreateSolver("GLOP")
    solver.SetNumThreads(1)
    solver.SetTimeLimit(1000)
    assert solver.SetSolverSpecificParametersAsString("random_seed: 2026104")
    xs = [solver.NumVar(0, 1, f"x_{i}") for i in range(1200)]
    for index, (ids, coefficients, lower, upper) in enumerate(rows):
        row = solver.Constraint(lower, upper if upper != prepare.INF else solver.infinity())
        for variable, coefficient in zip(ids, coefficients, strict=True):
            row.SetCoefficient(xs[variable], coefficient)
        for side, bound, coefficient in (("lo", lower, 1), ("hi", upper, -1)):
            if bound != prepare.INF:
                slack = solver.NumVar(0, solver.infinity(), f"{side}_{index}")
                row.SetCoefficient(slack, coefficient)
                solver.Objective().SetCoefficient(slack, 1)
    solver.Objective().SetMinimization()
    started = time.monotonic()
    status = solver.Solve()
    seconds = time.monotonic() - started
    labels = {
        0: "OPTIMAL",
        1: "FEASIBLE",
        2: "INFEASIBLE",
        3: "UNBOUNDED",
        4: "ABNORMAL",
        6: "NOT_SOLVED",
    }
    record = {
        "status": labels.get(status, str(status)),
        "seconds": seconds,
        "solver": solver.SolverVersion(),
        "time_limit_seconds": 1,
    }
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return record, None
    values = [variable.solution_value() for variable in xs]
    assert all(-1e-7 <= value <= 1 + 1e-7 for value in values)
    objective = solver.Objective().Value()
    residual = 0.0
    for ids, coefficients, lower, upper in rows:
        value = sum(
            coefficient * values[i] for i, coefficient in zip(ids, coefficients, strict=True)
        )
        residual += max(0.0, lower - value)
        if upper != prepare.INF:
            residual += max(0.0, value - upper)
    assert residual <= objective + 1e-5
    if status == pywraplp.Solver.OPTIMAL:
        assert abs(residual - objective) <= 1e-5
    record.update(objective=objective, recomputed_l1_residual=residual)
    return record, values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("gate", type=Path)
    args = parser.parse_args()
    proposal = json.loads((HERE / "proposal.json").read_text())
    gate = json.loads(args.gate.read_text())
    assert gate["passed"] and gate["proposal_sha256"] == prepare.sha(HERE / "proposal.json")
    assert gate["generator_sha256"] == prepare.sha(HERE / "prepare.py")
    assert proposal["source_sha256"] == prepare.sha(HERE / "prepare.py")
    for relative, expected in proposal["input_files"].items():
        assert prepare.sha(ROOT / relative) == expected
    assert not RAW.exists() and not (HERE / "result.json").exists()
    oracle = load(prepare.SOURCE, "switch_oracle")
    manifest = json.loads(prepare.MANIFEST.read_text())
    oracle.MODEL, oracle.WITNESS = ROOT / manifest["model"], prepare.SEED
    blocks, ordinary, heavy, fixed, basis_rows = oracle.rebuild()
    exact = load(prepare.LP_CORE, "switch_exact")
    cuts = json.loads(prepare.BUNDLE.read_text())["cuts"]
    initial_records, _ = prepare.ranked_neighbors(fixed, heavy, blocks, basis_rows, cuts)
    assert json.loads(json.dumps(initial_records)) == proposal["candidates"]
    RAW.mkdir()
    for path in (
        HERE / "prepare.py",
        Path(__file__),
        HERE / "proposal.json",
        args.gate,
        prepare.LP_CORE,
    ):
        (RAW / path.name).write_bytes(path.read_bytes())
    provenance = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "runner_sha256": prepare.sha(__file__),
        "proposal_sha256": prepare.sha(HERE / "proposal.json"),
        "gate_sha256": prepare.sha(args.gate),
        "ortools_version": ortools_version,
        "platform": platform.platform(),
        "budgets": {
            "rounds_max": 3,
            "lp_evaluations_max": 60,
            "solver_seconds_max": 30,
            "each_lp_seconds_max": 1,
            "workers": 1,
            "seed": 2026104,
        },
    }
    dump(RAW / "start.json", provenance)
    current = tuple(sorted(fixed))
    current_objective = proposal["baseline_elastic_objective"]
    cache = {
        prepare.data_hash(current): {
            "objective": current_objective,
            "status": "OPTIMAL",
            "cached_baseline": True,
        }
    }
    evaluations, solver_seconds = 0, 0.0
    rounds = []
    checked_primal = None
    stop_reason = "round_limit"
    for round_index in range(1, 4):
        neighbors, counts = prepare.ranked_neighbors(current, heavy, blocks, basis_rows, cuts)
        selected = neighbors[:20]
        directory = RAW / f"round-{round_index}"
        directory.mkdir()
        ranking = {
            "round": round_index,
            "current_heavy": current,
            "current_objective": current_objective,
            "counts": counts,
            "neighbors": neighbors,
            "selected_ranks": [r["rank"] for r in selected],
        }
        dump(directory / "ranking.json", ranking)
        best, best_objective = current, current_objective
        results = []
        for neighbor in selected:
            key = neighbor["heavy_sha256"]
            candidate = tuple(blocks[gid] for gid in neighbor["heavy_global_ids"])
            if key in cache:
                record = {**cache[key], "cached": True}
            else:
                # Leave a 1.1-second margin before a capped one-second solve.
                if evaluations >= 60 or solver_seconds >= 28.9:
                    stop_reason = "evaluation_or_solver_budget"
                    break
                rows = prepare.shifted_rows(basis_rows, heavy, candidate)
                assert prepare.data_hash(rows) == neighbor["shifted_rows_sha256"]
                record, values = solve(rows)
                evaluations += 1
                solver_seconds += record["seconds"]
                if values is not None:
                    vector_path = directory / f"rank-{neighbor['rank']:02d}-values.json"
                    dump(vector_path, values)
                    record.update(
                        vector_path=str(vector_path.relative_to(ROOT)),
                        vector_sha256=prepare.sha(vector_path),
                    )
                    if record["recomputed_l1_residual"] <= 1e-7:
                        for limit in (100, 10000, 1000000, 1000000000):
                            checked_primal = exact.exact_primal(rows, values, limit)
                            if checked_primal is not None:
                                checked_primal.update(
                                    heavy_global_ids=neighbor["heavy_global_ids"],
                                    ordinary_global_ids=proposal["ordinary_global_ids"],
                                    shifted_rows_sha256=neighbor["shifted_rows_sha256"],
                                )
                                dump(HERE / "exact-primal.json", checked_primal)
                                record["exact_primal_sha256"] = prepare.sha(
                                    HERE / "exact-primal.json"
                                )
                                stop_reason = "checked_exact_fractional_feasibility"
                                break
                cache[key] = record.copy()
            record.update(
                rank=neighbor["rank"],
                heavy_sha256=key,
                cut_lower_bound=neighbor["maximum_cut_lower_bound"],
            )
            if record["status"] == "OPTIMAL":
                numerator, denominator = neighbor["maximum_cut_lower_bound"]
                assert record["objective"] + 1e-5 >= numerator / denominator
                if record["objective"] < best_objective - 1e-7:
                    best, best_objective = candidate, record["objective"]
            results.append(record)
            dump(directory / "evaluations.json", results)
            if checked_primal is not None:
                best, best_objective = candidate, record["objective"]
                break
        improved = best_objective < current_objective - 1e-7
        report = {
            "round": round_index,
            "neighbors": len(neighbors),
            "selected": len(selected),
            "evaluated_or_cached": len(results),
            "objective_before": current_objective,
            "objective_after": best_objective,
            "improved": improved,
            "best_heavy_global_ids": [blocks.index(block) for block in best],
            "ranking_sha256": prepare.sha(directory / "ranking.json"),
            "results": results,
        }
        rounds.append(report)
        print(
            json.dumps({key: value for key, value in report.items() if key != "results"}),
            flush=True,
        )
        current, current_objective = best, best_objective
        if checked_primal is not None or stop_reason == "evaluation_or_solver_budget":
            break
        if not improved:
            stop_reason = "no_improvement_among_selected_neighbors"
            break
    result = {
        **provenance,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "initial_objective": proposal["baseline_elastic_objective"],
        "final_objective": current_objective,
        "best_heavy_global_ids": [blocks.index(block) for block in current],
        "lp_evaluations": evaluations,
        "solver_seconds": solver_seconds,
        "rounds": rounds,
        "stop_reason": stop_reason,
        "checked_exact_fractional_feasibility": checked_primal is not None,
        "covering_witness": False,
        "global_lower_bound_claim": False,
        "scope": (
            "Bounded regular four-sevenfold heavy neighborhood. "
            "This is not an exhaustive local optimum or a covering witness."
        ),
    }
    assert evaluations <= 60 and solver_seconds <= 30 and len(rounds) <= 3
    result["raw_sha256"] = {
        str(path.relative_to(RAW)): prepare.sha(path)
        for path in sorted(RAW.rglob("*"))
        if path.is_file()
    }
    dump(HERE / "result.json", result)
    print(
        json.dumps(
            {key: value for key, value in result.items() if key not in ("rounds", "raw_sha256")}
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
