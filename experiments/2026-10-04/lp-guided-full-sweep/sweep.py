# Document:    Complete Single Neighborhood LP Sweep with Bound Cached Results
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      624f7fd15ea8b673c504f748855435b8cba419bc8574bdaf9695ac8a183f3e1e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare or run one complete neighborhood; never begin a second neighborhood."""

import argparse
import importlib.util
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from ortools import __version__ as ortools_version
from ortools.linear_solver import pywraplp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PILOT = HERE.parent / "lp-guided-link-switch"
PILOT_RAW = ROOT / "experiments/scratch/lp-guided-link-switch-20261004"
RAW = ROOT / "experiments/scratch/lp-guided-full-sweep-20261004"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = load(PILOT / "prepare.py", "sweep_generator")
sha = generator.sha


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def basis():
    oracle = load(generator.SOURCE, "sweep_oracle")
    manifest = json.loads(generator.MANIFEST.read_text())
    oracle.MODEL, oracle.WITNESS = ROOT / manifest["model"], generator.SEED
    return oracle.rebuild()


def prepare():
    assert not (HERE / "proposal.json").exists()
    previous = json.loads((PILOT / "result.json").read_text())
    previous_proposal = json.loads((PILOT / "proposal.json").read_text())
    previous_check = json.loads((PILOT / "readback.json").read_text())
    assert previous_check["passed"] and previous_check["vectors_checked"] == 60
    assert previous_check["result_sha256"] == sha(PILOT / "result.json")
    assert previous["final_objective"] == 5.575882992498541
    for relative, expected in previous["raw_sha256"].items():
        assert sha(PILOT_RAW / relative) == expected
    for relative, expected in previous_proposal["input_files"].items():
        assert sha(ROOT / relative) == expected
    blocks, ordinary, heavy, _, rows = basis()
    fixed = [blocks[index] for index in previous["best_heavy_global_ids"]]
    cuts = json.loads(generator.BUNDLE.read_text())["cuts"]
    neighbors, counts = generator.ranked_neighbors(fixed, heavy, blocks, rows, cuts)
    final_ranking = json.loads((PILOT_RAW / "round-3/ranking.json").read_text())
    assert json.loads(json.dumps(neighbors)) == final_ranking["neighbors"]
    cache = {}
    for round_record in previous["rounds"]:
        folder = PILOT_RAW / f"round-{round_record['round']}"
        ranking = json.loads((folder / "ranking.json").read_text())
        for record in round_record["results"]:
            assert record["status"] == "OPTIMAL"
            neighbor = ranking["neighbors"][record["rank"]]
            assert record["heavy_sha256"] == neighbor["heavy_sha256"]
            assert sha(ROOT / record["vector_path"]) == record["vector_sha256"]
            assert neighbor["heavy_sha256"] not in cache
            cache[neighbor["heavy_sha256"]] = {
                "record": record,
                "neighbor": neighbor,
                "source_round": round_record["round"],
                "ranking_path": str((folder / "ranking.json").relative_to(ROOT)),
                "ranking_sha256": sha(folder / "ranking.json"),
            }
    matches = {}
    for neighbor in neighbors:
        if neighbor["heavy_sha256"] in cache:
            cached = cache[neighbor["heavy_sha256"]]
            assert cached["neighbor"]["heavy_global_ids"] == neighbor["heavy_global_ids"]
            assert cached["neighbor"]["shifted_rows_sha256"] == neighbor["shifted_rows_sha256"]
            matches[neighbor["heavy_sha256"]] = cached
    assert len(neighbors) == 136 and len(matches) == 23
    inputs = {
        str(path.relative_to(ROOT)): sha(path)
        for path in (
            PILOT / "prepare.py",
            PILOT / "run.py",
            PILOT / "result.json",
            PILOT / "readback.json",
            PILOT / "proposal.json",
            generator.SOURCE,
            generator.LP_CORE,
            generator.BUNDLE,
            generator.CUT_GATE,
        )
    }
    inputs.update(previous_proposal["input_files"])
    proposal = {
        "source_sha256": sha(__file__),
        "input_files": inputs,
        "baseline_heavy_global_ids": previous["best_heavy_global_ids"],
        "baseline_elastic_objective": previous["final_objective"],
        "ordinary_global_ids": [blocks.index(block) for block in ordinary],
        "neighborhood_count": len(neighbors),
        "enumeration_counts": counts,
        "neighbors": neighbors,
        "cached": matches,
        "cached_count": len(matches),
        "fresh_calls_expected": len(neighbors) - len(matches),
        "budgets": {
            "one_neighborhood": True,
            "each_lp_seconds": 1,
            "solver_seconds": 40,
            "wall_seconds": 60,
            "workers": 1,
            "seed": 2026104,
        },
        "optimizer_calls": 0,
    }
    dump(HERE / "proposal.json", proposal)
    print(
        json.dumps(
            {
                "proposal_sha256": sha(HERE / "proposal.json"),
                "source_sha256": sha(__file__),
                "neighbors": len(neighbors),
                "cache": len(matches),
                "fresh": len(neighbors) - len(matches),
            }
        )
    )


def solve(rows):
    solver = pywraplp.Solver.CreateSolver("GLOP")
    solver.SetNumThreads(1)
    solver.SetTimeLimit(1000)
    assert solver.SetSolverSpecificParametersAsString("random_seed: 2026104")
    xs = [solver.NumVar(0, 1, f"x_{i}") for i in range(1200)]
    constraints = []
    for index, (ids, coefficients, lower, upper) in enumerate(rows):
        row = solver.Constraint(lower, upper if upper != generator.INF else solver.infinity())
        for variable, coefficient in zip(ids, coefficients, strict=True):
            row.SetCoefficient(xs[variable], coefficient)
        for side, bound, coefficient in (("lo", lower, 1), ("hi", upper, -1)):
            if bound != generator.INF:
                slack = solver.NumVar(0, solver.infinity(), f"{side}_{index}")
                row.SetCoefficient(slack, coefficient)
                solver.Objective().SetCoefficient(slack, 1)
        constraints.append(row)
    solver.Objective().SetMinimization()
    before = time.monotonic()
    status = solver.Solve()
    elapsed = time.monotonic() - before
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
        "seconds": elapsed,
        "solver": solver.SolverVersion(),
        "time_limit_seconds": 1,
    }
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return record, None, None
    values = [variable.solution_value() for variable in xs]
    dual = [row.dual_value() for row in constraints]
    assert all(-1e-7 <= value <= 1 + 1e-7 for value in values)
    residual = 0.0
    for ids, coefficients, lower, upper in rows:
        value = sum(
            coefficient * values[index]
            for index, coefficient in zip(ids, coefficients, strict=True)
        )
        residual += max(0.0, lower - value)
        if upper != generator.INF:
            residual += max(0.0, value - upper)
    objective = solver.Objective().Value()
    assert residual <= objective + 1e-5
    if status == pywraplp.Solver.OPTIMAL:
        assert abs(residual - objective) <= 1e-5
    record.update(objective=objective, recomputed_l1_residual=residual)
    return record, values, dual


def run(gate_path):
    wall_started = time.monotonic()
    proposal = json.loads((HERE / "proposal.json").read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] and gate["proposal_sha256"] == sha(HERE / "proposal.json")
    assert gate["source_sha256"] == sha(__file__) == proposal["source_sha256"]
    for relative, expected in proposal["input_files"].items():
        assert sha(ROOT / relative) == expected
    assert not RAW.exists() and not (HERE / "result.json").exists()
    blocks, _, heavy, _, rows = basis()
    exact = load(generator.LP_CORE, "sweep_exact")
    RAW.mkdir()
    for path in (Path(__file__), HERE / "proposal.json", gate_path, generator.LP_CORE):
        (RAW / path.name).write_bytes(path.read_bytes())
    start = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": sha(__file__),
        "proposal_sha256": sha(HERE / "proposal.json"),
        "gate_sha256": sha(gate_path),
        "ortools_version": ortools_version,
        "budgets": proposal["budgets"],
    }
    dump(RAW / "start.json", start)
    evaluated, fresh, cached, solver_seconds = [], 0, 0, 0.0
    best_ids = proposal["baseline_heavy_global_ids"]
    best_objective = proposal["baseline_elastic_objective"]
    exact_primal = None
    stop_reason = "complete_neighborhood"
    for neighbor in proposal["neighbors"]:
        key = neighbor["heavy_sha256"]
        if key in proposal["cached"]:
            binding = proposal["cached"][key]
            record = binding["record"].copy()
            assert record["status"] == "OPTIMAL"
            assert sha(ROOT / record["vector_path"]) == record["vector_sha256"]
            record.update(cached=True, source_round=binding["source_round"])
            cached += 1
        else:
            if solver_seconds >= 38.9 or time.monotonic() - wall_started >= 58.9:
                stop_reason = "solver_or_wall_budget"
                break
            fixed = [blocks[index] for index in neighbor["heavy_global_ids"]]
            shifted = generator.shifted_rows(rows, heavy, fixed)
            assert generator.data_hash(shifted) == neighbor["shifted_rows_sha256"]
            record, values, dual = solve(shifted)
            fresh += 1
            solver_seconds += record["seconds"]
            record["cached"] = False
            if values is not None:
                vector_path = RAW / f"rank-{neighbor['rank']:03d}-values.json"
                dual_path = RAW / f"rank-{neighbor['rank']:03d}-dual.json"
                dump(vector_path, values)
                dump(dual_path, dual)
                record.update(
                    vector_path=str(vector_path.relative_to(ROOT)),
                    vector_sha256=sha(vector_path),
                    dual_path=str(dual_path.relative_to(ROOT)),
                    dual_sha256=sha(dual_path),
                )
                if record["recomputed_l1_residual"] <= 1e-7:
                    for limit in (100, 10000, 1000000, 1000000000):
                        exact_primal = exact.exact_primal(shifted, values, limit)
                        if exact_primal is not None:
                            exact_primal.update(
                                heavy_global_ids=neighbor["heavy_global_ids"],
                                ordinary_global_ids=proposal["ordinary_global_ids"],
                                shifted_rows_sha256=neighbor["shifted_rows_sha256"],
                            )
                            dump(HERE / "exact-primal.json", exact_primal)
                            record["exact_primal_sha256"] = sha(HERE / "exact-primal.json")
                            stop_reason = "checked_exact_fractional_feasibility"
                            break
        record.update(
            rank=neighbor["rank"],
            heavy_sha256=key,
            heavy_global_ids=neighbor["heavy_global_ids"],
            shifted_rows_sha256=neighbor["shifted_rows_sha256"],
        )
        if record["status"] == "OPTIMAL":
            numerator, denominator = neighbor["maximum_cut_lower_bound"]
            assert record["objective"] + 1e-5 >= numerator / denominator
            if record["objective"] < best_objective - 1e-7:
                best_objective, best_ids = record["objective"], neighbor["heavy_global_ids"]
        evaluated.append(record)
        dump(RAW / "evaluations.json", evaluated)
        if exact_primal is not None:
            best_ids, best_objective = neighbor["heavy_global_ids"], record["objective"]
            break
    wall_seconds = time.monotonic() - wall_started
    result = {
        **start,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "initial_objective": proposal["baseline_elastic_objective"],
        "best_objective": best_objective,
        "best_heavy_global_ids": best_ids,
        "neighborhood_count": proposal["neighborhood_count"],
        "evaluated_count": len(evaluated),
        "fresh_evaluations": fresh,
        "cached_evaluations": cached,
        "solver_seconds": solver_seconds,
        "wall_seconds": wall_seconds,
        "stop_reason": stop_reason,
        "complete_neighborhood": len(evaluated) == proposal["neighborhood_count"],
        "exact_fractional_feasibility": exact_primal is not None,
        "covering_witness": False,
        "global_lower_bound_claim": False,
        "records": evaluated,
    }
    assert solver_seconds <= 40 and wall_seconds <= 60
    result["raw_sha256"] = {
        str(path.relative_to(RAW)): sha(path) for path in sorted(RAW.iterdir()) if path.is_file()
    }
    dump(HERE / "result.json", result)
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
