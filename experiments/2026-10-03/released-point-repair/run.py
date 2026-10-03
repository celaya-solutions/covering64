# Document:    Released Point Neighborhood Repair
# Version:     v1.0.1
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Fix blocks avoiding chosen points; allow every other block without regularity assumptions."""

import argparse
import hashlib
import json
import math
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import ortools
from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model

from covering64.core import Universe, read_blocks, verify_cover, write_blocks

ROOT = Path(__file__).resolve().parents[3]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_candidate(blocks, path):
    write_blocks(path, blocks)
    package = verify_cover(blocks)
    run = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_cover.py"), str(path),
         "--expected-blocks", "64"],
        capture_output=True, text=True,
    )
    require(run.returncode in (0, 1), "standalone verifier failed")
    standalone = json.loads(run.stdout)
    require(len(blocks) == 64 and package["canonical_sha256"] == standalone["canonical_sha256"]
            and len(package["uncovered"]) == standalone["uncovered_count"], "checkers disagree")
    return {"package": package, "standalone": standalone}


def residual_dual(universe, deficient, candidates, budget):
    solver = pywraplp.Solver.CreateSolver("GLOP")
    solver.SetTimeLimit(10000)
    weights = {t: solver.NumVar(0, solver.infinity(), f"triple_{t}") for t in deficient}
    for i in candidates:
        row = solver.RowConstraint(-solver.infinity(), 1, "")
        for t in universe.coverage[i]:
            if t in weights:
                row.SetCoefficient(weights[t], 1)
    solver.Maximize(sum(weights.values()))
    status = solver.Solve()
    numerators = {}
    if status in (solver.OPTIMAL, solver.FEASIBLE):
        numerators = {t: max(0, math.floor(value.solution_value() * 1000000))
                      for t, value in weights.items()}
        numerators = {t: value for t, value in numerators.items() if value}
    loads = [sum(numerators.get(t, 0) for t in universe.coverage[i]) for i in candidates]
    denominator = max(1000000, max(loads, default=0))
    bound = Fraction(sum(numerators.values()), denominator)
    require(all(load <= denominator for load in loads), "dual column capacity violated")
    return {"solver_status": status, "weights": sorted(numerators.items()),
            "common_denominator": denominator, "bound": [bound.numerator, bound.denominator],
            "addition_budget": budget, "proves_neighborhood_infeasible": bound > budget,
            "columns_checked": len(candidates),
            "scope": "Only the stated retained-block neighborhood"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--points", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=2026102901)
    args = parser.parse_args()
    points = [int(p) for p in args.points.split(",")]
    require(points and len(set(points)) == len(points) and all(1 <= p <= 16 for p in points),
            "release points must be distinct labels1..16")
    require(math.isfinite(args.seconds) and 0 < args.seconds <= 300, "invalid budget")
    require(1 <= args.workers <= 4, "invalid workers")
    args.output.mkdir(parents=True, exist_ok=True)
    universe = Universe.build()
    original = read_blocks(args.candidate)
    initial = check_candidate(original, args.output / "initial.txt")
    rank = {block: i for i, block in enumerate(universe.blocks)}
    selected = {rank[block] for block in original}
    released = set(points)
    retained = sorted(i for i in selected if not released.intersection(universe.blocks[i]))
    candidates = [i for i, block in enumerate(universe.blocks) if released.intersection(block)]
    covered = {t for i in retained for t in universe.coverage[i]}
    deficient = sorted(set(range(560)) - covered)
    budget = 64 - len(retained)
    model = cp_model.CpModel()
    xs = {i: model.new_bool_var(f"block_{i}") for i in candidates}
    for t in deficient:
        model.add(sum(xs[i] for i in universe.containing[t] if i in xs) >= 1)
    model.add(sum(xs.values()) == budget)
    for i, x in xs.items():
        model.add_hint(x, int(i in selected))
    model_path = args.output / "model.pbtxt"
    model.export_to_file(str(model_path))
    require(model.validate() == "", "invalid CP model")
    certificate = residual_dual(universe, deficient, candidates, budget)
    (args.output / "dual.json").write_text(json.dumps(certificate, indent=2) + "\n")
    sources = {}
    for path in (Path(__file__), ROOT / "scripts/check_cover.py", ROOT / "src/covering64/core.py"):
        snapshot = args.output / path.name
        snapshot.write_bytes(path.read_bytes())
        sources[path.name] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    metadata = {
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "sources": sources, "input": str(args.candidate),
        "input_sha256": hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
        "initial": initial, "release_points": sorted(points), "retained_ids": retained,
        "candidate_ids": candidates, "deficient_ids": deficient, "addition_budget": budget,
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "solver_version": ortools.__version__, "seconds": args.seconds, "workers": args.workers,
        "seed": args.seed, "command": sys.argv,
        "scope": "Retain exactly the input blocks avoiding the release points; "
        "every added block must touch a release point. "
        "All blocks touching a release point are permitted; "
        "no regularity or heavy-profile constraints.",
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({"retained": len(retained), "choices": len(candidates), "budget": budget,
                      "deficient": len(deficient),
                      "dual_bound": str(Fraction(*certificate["bound"])),
                      "dual_excludes": certificate["proves_neighborhood_infeasible"]}), flush=True)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = args.seed
    solver.parameters.repair_hint = True
    solver.parameters.hint_conflict_limit = 10000
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    (args.output / "parameters.txt").write_text(str(solver.parameters))
    with (args.output / "solver.log").open("w") as log:
        solver.log_callback = lambda line: (log.write(line + "\n"), log.flush())
        status = solver.solve(model)
    result = {"status": solver.status_name(status), "seconds": solver.wall_time,
              "response_stats": solver.response_stats(), "cover_found": False,
              "dual_bound": certificate["bound"],
              "dual_excludes": certificate["proves_neighborhood_infeasible"]}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        ids = sorted(set(retained) | {i for i, x in xs.items() if solver.value(x)})
        candidate = [universe.blocks[i] for i in ids]
        checked = check_candidate(candidate, args.output / "candidate.txt")
        require(checked["package"]["valid"] and checked["standalone"]["valid"], "not a cover")
        result.update(cover_found=True, checks=checked)
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "response_stats"}), flush=True)


if __name__ == "__main__":
    main()
