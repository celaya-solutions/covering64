# Document:    Primal Inspection of Remaining First-Link Linear Programs
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Inspect only previously feasible cases, save primals, and verify top64 rounding."""

import argparse
import gzip
import hashlib
import json
import math
import shutil
import subprocess
import sys
from itertools import combinations
from pathlib import Path

import ortools
from ortools.linear_solver import pywraplp

from covering64.core import verify_cover, write_blocks

ROOT = Path(__file__).resolve().parents[3]
EPSILON = 1e-7


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solve_primal(rows, width, seconds):
    solver = pywraplp.Solver.CreateSolver("GLOP")
    solver.SetTimeLimit(max(1, round(seconds * 1000)))
    variables = [solver.NumVar(0, 1, f"x{i}") for i in range(width)]
    for ids, coefficients, lower, upper in rows:
        row = solver.RowConstraint(lower if lower is not None else -solver.infinity(),
                                   upper if upper is not None else solver.infinity(), "")
        for index, coefficient in zip(ids, coefficients):
            row.SetCoefficient(variables[index], coefficient)
    solver.Objective().SetMinimization()
    status = solver.Solve()
    summary = {"status": status, "milliseconds": solver.wall_time()}
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return summary, None
    values = [v.solution_value() for v in variables]
    require(all(math.isfinite(value) for value in values), "nonfinite primal value")
    domain_violation = max(max(-value, value - 1, 0) for value in values)
    row_violation = 0
    for ids, coefficients, lower, upper in rows:
        total = math.fsum(values[i] * coefficient for i, coefficient in zip(ids, coefficients))
        row_violation = max(row_violation, 0 if lower is None else lower - total,
                            0 if upper is None else total - upper)
    block_values = values[:4368]
    clipped = [min(1, max(0, value)) for value in block_values]
    fractional = [value for value in clipped if EPSILON < value < 1 - EPSILON]
    summary.update(
        objective=solver.Objective().Value(), max_domain_violation=domain_violation,
        max_row_violation=row_violation,
        numerically_valid=domain_violation <= EPSILON and row_violation <= EPSILON,
        block_sum=math.fsum(block_values), double_sum=math.fsum(values[4368:]),
        fractional_block_mass=math.fsum(min(value, 1 - value) for value in clipped),
        fractional_block_count=len(fractional),
        near_one_blocks=sum(value >= 1 - EPSILON for value in clipped),
        near_zero_blocks=sum(value <= EPSILON for value in clipped),
        threshold_half_count=sum(value >= 0.5 for value in clipped),
        fractional_double_count=sum(EPSILON < value < 1 - EPSILON for value in values[4368:]),
    )
    return summary, values


def verify_rounding(values, blocks, output, checker):
    ids = sorted(sorted(range(4368), key=lambda i: (-values[i], i))[:64])
    candidate = [blocks[i] for i in ids]
    path = output / "rounded-top64.txt"
    write_blocks(path, candidate)
    package = verify_cover(candidate)
    run = subprocess.run([sys.executable, str(checker), str(path), "--expected-blocks", "64"],
                         capture_output=True, text=True)
    require(run.returncode in (0, 1), "standalone verifier crashed")
    standalone = json.loads(run.stdout)
    require(package["canonical_sha256"] == standalone["canonical_sha256"], "hash disagreement")
    require(len(package["uncovered"]) == standalone["uncovered_count"], "deficit disagreement")
    require(package["valid"] == standalone["valid"], "validity disagreement")
    (output / "rounded-checks.json").write_text(json.dumps(
        {"package": package, "standalone": standalone}, indent=2) + "\n")
    return {"method": "64 largest raw block values; tie by global lexicographic block ID",
            "ids": ids, "block_count": len(candidate), "uncovered_count": len(package["uncovered"]),
            "package_valid": package["valid"], "standalone_valid": standalone["valid"],
            "canonical_sha256": package["canonical_sha256"], "candidate_sha256": digest(path),
            "checks_sha256": digest(output / "rounded-checks.json")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("screen", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=10)
    args = parser.parse_args()
    require(math.isfinite(args.seconds) and args.seconds > 0, "invalid budget")
    require(not args.output.exists(), "output must be new")
    args.output.mkdir(parents=True)
    screen = json.loads(gzip.decompress((args.screen / "results.json.gz").read_bytes()))
    remaining = [entry for entry in screen if not entry["proves_infeasible"]
                 and entry["feasibility_lp"]["status"] in (0, 1)]
    require(len(screen) == 258 and len(remaining) == 158, "unexpected screen count")
    require({case: sum(item["case"] == case for item in remaining)
             for case in ("cycle", "matching")} == {"cycle": 102, "matching": 56},
            "unexpected remaining cases")
    blocks = list(combinations(range(1, 17), 5))
    block_ranks = {block: i for i, block in enumerate(blocks)}
    representatives = json.loads((args.screen / "representatives.json").read_text())
    expected = {rep["id"]: [block_ranks[(1, 2, 3, *edge)] for edge in rep["edges"]]
                for case in representatives["cases"] for rep in case["representatives"]}
    require(len({item["id"] for item in remaining}) == 158, "duplicate case")
    require(all(item["fixed_ids"] == expected[item["id"]] for item in remaining),
            "fixed IDs disagree with representatives")
    sources = {}
    for path in (Path(__file__), ROOT / "scripts/check_cover.py", ROOT / "src/covering64/core.py"):
        shutil.copyfile(path, args.output / path.name)
        sources[path.name] = digest(path)
    inputs = {}
    for name in ("results.json.gz", "representatives.json", "metadata.json",
                 "cycle-rows.json.gz", "matching-rows.json.gz",
                 "cycle-base.pbtxt", "matching-base.pbtxt"):
        path = args.screen / name
        shutil.copyfile(path, args.output / f"input-{name}")
        inputs[name] = digest(path)
    metadata = {
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "sources": sources, "inputs": inputs, "solver_version": ortools.__version__,
        "screen_directory": str(args.screen), "command": sys.argv, "seconds_per_lp": args.seconds,
        "epsilon": EPSILON, "cases": {"cycle": 102, "matching": 56},
        "ranking": "ascending fractional_block_mass, fractional_block_count, rounded deficit, ID",
        "scope": "Numerical primal inspection of158 previously LP-feasible fixed first-link "
        "cases in the normalized regular four-sevenfold branch. Rounding is independently "
        "verified as a block set; LP feasibility and ranking are not proofs or covers.",
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    bases = {case: json.loads(gzip.decompress(
        (args.screen / f"{case}-rows.json.gz").read_bytes())) for case in ("cycle", "matching")}
    results = []
    for entry in remaining:
        output = args.output / entry["id"]
        output.mkdir()
        base = bases[entry["case"]]
        require(base["width"] == 4768 and len(base["rows"]) == 4270, "unexpected base model")
        rows = base["rows"] + [[[i], [1], 1, 1] for i in entry["fixed_ids"]]
        summary, values = solve_primal(rows, base["width"], args.seconds)
        result = {"id": entry["id"], "case": entry["case"], "fixed_ids": entry["fixed_ids"],
                  "lp": summary, "rounding": None, "primal_sha256": None}
        if values is not None:
            payload = {"id": entry["id"], "case": entry["case"], "values": values,
                       "fixed_ids": entry["fixed_ids"], "rows": len(rows), "width": base["width"]}
            primal_path = output / "primal.json.gz"
            primal_path.write_bytes(gzip.compress((json.dumps(payload) + "\n").encode(), mtime=0))
            result["primal_sha256"] = digest(primal_path)
            result["rounding"] = verify_rounding(values, blocks, output,
                                                 args.output / "check_cover.py")
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        results.append(result)
        (args.output / "results.json.gz").write_bytes(gzip.compress(
            (json.dumps(results, indent=2) + "\n").encode(), mtime=0))
        print(json.dumps({"id": result["id"], "lp_status": summary["status"],
                          "fractional_mass": summary.get("fractional_block_mass"),
                          "fractional_count": summary.get("fractional_block_count"),
                          "rounded_holes": None if result["rounding"] is None else
                          result["rounding"]["uncovered_count"]}), flush=True)
    eligible = [item for item in results if item["lp"].get("numerically_valid")]
    ranking = sorted(eligible, key=lambda item: (item["lp"]["fractional_block_mass"],
                     item["lp"]["fractional_block_count"], item["rounding"]["uncovered_count"],
                     item["id"]))
    (args.output / "ranking.json").write_text(json.dumps(ranking, indent=2) + "\n")


if __name__ == "__main__":
    main()
