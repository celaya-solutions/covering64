# Document:    Independent MIP search for covering degree branches
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""SCIP searches; numerical solver statuses are not independently checked proofs."""

import argparse
import hashlib
import json
import math
import subprocess
import sys
from itertools import combinations
from pathlib import Path

from ortools.linear_solver import pywraplp

from covering64.core import Universe, read_blocks, verify_cover, write_blocks


def build_model(branch, target=64, normalize_regular=False):
    if branch not in ("unrestricted", "regular20", "degree19"):
        raise ValueError("Unknown branch")
    if type(target) is not int or target < 0:
        raise ValueError("Target must be nonnegative integer")
    if normalize_regular and branch != "regular20":
        raise ValueError("First-block normalization is only enabled in the regular branch")
    universe = Universe.build()
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if solver is None:
        raise RuntimeError("SCIP is unavailable")
    variables = [solver.BoolVar(f"block_{i}") for i in range(len(universe.blocks))]
    excess = {(2, x) for x in range(3, 7)} | {(x, x + 1) for x in range(7, 17, 2)}
    for triple, containing in zip(universe.triples, universe.containing):
        row = sum(variables[i] for i in containing)
        if branch == "degree19" and triple[0] == 1:
            solver.Add(row == (2 if triple[1:] in excess else 1))
        else:
            solver.Add(row >= 1)
    solver.Add(sum(variables) <= target)
    if branch == "regular20":
        # Summing the sixteen degree equations gives 5*b=16*20.
        solver.Add(sum(variables) == 64)
        if normalize_regular:
            # Every regular cover contains a block; relabel its points to 1..5.
            # Degree 20 at every point is invariant under this permutation.
            solver.Add(variables[0] == 1)
    for point in range(1, 17):
        row = sum(variables[i] for i, block in enumerate(universe.blocks) if point in block)
        if branch == "regular20":
            solver.Add(row == 20)
        elif branch == "degree19" and point == 1:
            solver.Add(row == 19)
        else:
            solver.Add(row >= 19)
    for a, b in combinations(range(1, 17), 2):
        solver.Add(sum(variables[i] for i, block in enumerate(universe.blocks)
                       if a in block and b in block) >= 5)
    return universe, solver, variables


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("branch", choices=["unrestricted", "regular20", "degree19"])
    parser.add_argument("--target", type=int, default=64)
    parser.add_argument("--seconds", type=float, default=1200)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--hint", type=Path)
    parser.add_argument("--fix-hint", action="store_true", help="Restrict to a positive control")
    parser.add_argument("--normalize-regular", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0 or not 0 <= args.seed < 2147483647:
        parser.error("Invalid time budget or seed")
    universe, solver, variables = build_model(args.branch, args.target, args.normalize_regular)
    solver.SetTimeLimit(int(args.seconds * 1000))
    solver.SetNumThreads(1)
    params = f"randomization/randomseedshift = {args.seed}\n"
    if not solver.SetSolverSpecificParametersAsString(params):
        raise RuntimeError("SCIP rejected its recorded parameters")
    mapping = None
    if args.hint:
        hint = read_blocks(args.hint)
        if args.normalize_regular:
            chosen = min(hint)
            order = list(chosen) + [p for p in range(1, 17) if p not in chosen]
            mapping = {p: i + 1 for i, p in enumerate(order)}
            hint = [tuple(sorted(mapping[p] for p in block)) for block in hint]
        selected = set(hint)
        values = [int(b in selected) for b in universe.blocks]
        solver.SetHint(variables, values)
        if args.fix_hint:
            for variable, value in zip(variables, values):
                solver.Add(variable == value)
    elif args.fix_hint:
        parser.error("--fix-hint requires a hint")
    args.output.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).read_bytes()
    (args.output / "source_snapshot.py").write_bytes(source)
    model = solver.ExportModelAsLpFormat(False)
    (args.output / "model.lp").write_text(model)
    metadata = {"branch": args.branch, "target": args.target, "seconds": args.seconds,
                "seed": args.seed, "threads": 1, "solver": solver.SolverVersion(),
                "fixed_control": args.fix_hint, "model_sha256": hashlib.sha256(
                    model.encode()).hexdigest(),
                "source_sha256": hashlib.sha256(source).hexdigest(),
                "source_revision": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True).strip(),
                "hint_sha256": hashlib.sha256(args.hint.read_bytes()).hexdigest()
                if args.hint else None,
                "normalize_regular": args.normalize_regular, "hint_permutation": mapping,
                "scope": "specified degree branch or control; no checked UNSAT proof"}
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    solver.EnableOutput()
    status = solver.Solve()
    names = {0: "OPTIMAL", 1: "FEASIBLE", 2: "INFEASIBLE", 3: "UNBOUNDED",
             4: "ABNORMAL", 5: "MODEL_INVALID", 6: "NOT_SOLVED"}
    result = {"status": names.get(status, str(status)), "wall_ms": solver.WallTime(),
              "nodes": solver.nodes(), "scope": metadata["scope"], "witness": None}
    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        witness = [b for b, variable in zip(universe.blocks, variables)
                   if variable.solution_value() > 0.5]
        verified = verify_cover(witness)
        if not verified["valid"] or len(witness) > args.target:
            raise RuntimeError("Numerical candidate failed exact package verification")
        path = args.output / "cover.txt"
        write_blocks(path, witness)
        independent = subprocess.run([sys.executable, "scripts/check_cover.py", str(path),
                                      "--expected-blocks", str(len(witness))],
                                     capture_output=True, text=True, check=True)
        result.update(witness=witness, verification=verified,
                      independent=json.loads(independent.stdout))
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
