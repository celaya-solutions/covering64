# Document:    Hinted Fixed First-Family Optimization
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      319a16efe3bae7655df25cfec19c57268c7a4c504edf4f54926a7410f0001dc7
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Improve a verified feasible partial state in an audited fixed-family model."""

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

import ortools
from first_family_hub_cuts import add_normalized_hub_cuts
from first_family_residual_cuts import add_residual_pair_cuts, residual_hint_values
from first_family_search import G, build_model
from heavy_triple_search import add_heavy_count_cuts
from ortools.sat.python import cp_model

from covering64.core import read_blocks, verify_cover, write_blocks


def check(blocks, path):
    write_blocks(path, blocks)
    package = verify_cover(blocks)
    proc = subprocess.run(
        [sys.executable, "scripts/check_cover.py", str(path), "--expected-blocks", "64"],
        capture_output=True,
        text=True,
    )
    if proc.returncode not in (0, 1):
        raise RuntimeError(proc.stderr)
    standalone = json.loads(proc.stdout)
    if len(blocks) != 64 or len(package["uncovered"]) != standalone["uncovered_count"]:
        raise ValueError("candidate check failed")
    if Counter(p for b in blocks for p in b) != Counter({p: 20 for p in range(1, 17)}):
        raise ValueError("degree20 check failed")
    return {"package": package, "standalone": standalone}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family", type=Path)
    parser.add_argument("hint", type=Path)
    parser.add_argument("--seconds", type=float, default=300)
    parser.add_argument("--seed", type=int, default=2026102101)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--lns-only", action="store_true")
    parser.add_argument("--residual-cuts", action="store_true")
    parser.add_argument("--heavy-count-cuts", action="store_true")
    parser.add_argument("--hub-cuts", action="store_true")
    parser.add_argument(
        "--relax-partial",
        action="store_true",
        help="Allow outside pair deficits and omit the opposite-spoke requirement"
        " in partial states",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0 or args.workers < 1:
        parser.error("positive finite time budget and positive worker count required")
    if args.hub_cuts and not args.heavy_count_cuts:
        parser.error("--hub-cuts requires --heavy-count-cuts")
    args.output.mkdir(parents=True, exist_ok=True)
    family = read_blocks(args.family, v=16, k=4)
    start = read_blocks(args.hint)
    initial = check(start, args.output / "initial.txt")
    max_missing = initial["standalone"]["uncovered_count"]
    universe, model, xs, holes = build_model(
        family,
        max_missing,
        require_outside_pair_bound=not args.relax_partial,
        require_opposite_spoke=not args.relax_partial,
    )
    ids = {i for i, block in enumerate(universe.blocks) if block in set(start)}
    values = {x.name: int(i in ids) for i, x in enumerate(xs)}
    coverage = Counter(t for i in ids for t in universe.coverage[i])
    values.update({x.name: int(coverage[t] == 0) for t, x in enumerate(holes)})
    if args.residual_cuts:
        add_residual_pair_cuts(universe, model, xs, holes)
        values.update(residual_hint_values(universe, start))
    if args.heavy_count_cuts:
        add_heavy_count_cuts(universe, model, xs)
        values.update({f"heavy6_{t}": int(coverage[t] >= 6)
                       for t in range(len(universe.triples))})
        values.update({f"heavy7_{t}": int(coverage[t] >= 7)
                       for t in range(len(universe.triples))})
    if args.hub_cuts:
        add_normalized_hub_cuts(universe, model, xs)
    for a in (2, 3):
        local = [
            tuple(p for p in b if p != a) for b in start if a in b and len(set(b) & {1, 2, 3}) == 1
        ]
        pairs = Counter(pair for b in local for pair in combinations(b, 2))
        values.update({f"local_hole_{a}_{pair}": int(pairs[pair] == 0) for pair in G})
        values[f"local_deficit_{a}"] = sum(pairs[pair] == 0 for pair in G)
    fixed = model.clone()
    for index, variable in enumerate(model.proto.variables):
        if variable.name not in values:
            raise RuntimeError(f"no hint value for {variable.name}")
        value = values[variable.name]
        model.add_hint(model.get_int_var_from_proto_index(index), value)
        fixed.add(fixed.get_int_var_from_proto_index(index) == value)
    checker = cp_model.CpSolver()
    checker.parameters.num_search_workers = 1
    checker.parameters.max_time_in_seconds = 10
    validation = checker.solve(fixed)
    if validation != cp_model.OPTIMAL:
        raise ValueError("complete hint is not a verified feasible model assignment")
    sources = {}
    for name in ["first_family_hint_search.py", "first_family_search.py",
                 "first_family_residual_cuts.py", "heavy_triple_search.py",
                 "first_family_hub_cuts.py"]:
        raw = Path(__file__).with_name(name).read_bytes()
        (args.output / name).write_bytes(raw)
        sources[name] = hashlib.sha256(raw).hexdigest()
    model_file = args.output / "model.pbtxt"
    model.export_to_file(str(model_file))
    metadata = {
        "sources": sources,
        "solver_version": ortools.__version__,
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "seed": args.seed,
        "seconds": args.seconds,
        "workers": args.workers,
        "lns_only": args.lns_only,
        "relax_partial": args.relax_partial,
        "residual_cuts": args.residual_cuts,
        "heavy_count_cuts": args.heavy_count_cuts,
        "hub_cuts": args.hub_cuts,
        "require_outside_pair_bound": not args.relax_partial,
        "require_opposite_spoke": not args.relax_partial,
        "family_sha256": hashlib.sha256(args.family.read_bytes()).hexdigest(),
        "hint_sha256": hashlib.sha256(args.hint.read_bytes()).hexdigest(),
        "hint_assignment_variables": len(values),
        "hint_validation": "OPTIMAL",
        "model_sha256": hashlib.sha256(model_file.read_bytes()).hexdigest(),
        "initial": initial,
        "scope": "Fixed-first-family partial optimization only.",
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")

    class Capture(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()
            self.best = max_missing + 1
            self.records = []

        def on_solution_callback(self):
            missing = sum(self.value(x) for x in holes)
            if missing >= self.best:
                return
            blocks = [b for i, b in enumerate(universe.blocks) if self.value(xs[i])]
            checked = check(blocks, args.output / f"candidate-h{missing}.txt")
            if checked["standalone"]["uncovered_count"] != missing:
                raise RuntimeError("objective check failed")
            self.best = missing
            self.records.append({"missing": missing, "seconds": self.wall_time, "checks": checked})
            (args.output / "improvements.json").write_text(
                json.dumps(self.records, indent=2) + "\n"
            )
            print(json.dumps({"missing": missing, "seconds": self.wall_time}), flush=True)

    capture = Capture()
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = args.workers
    solver.parameters.use_lns_only = args.lns_only
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.random_seed = args.seed
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    (args.output / "solver-parameters.txt").write_text(str(solver.parameters))
    with (args.output / "solver.log").open("w") as log:
        solver.log_callback = lambda line: log.write(line + "\n")
        status = solver.solve(model, capture)
    result = {
        "status": solver.status_name(status),
        "seconds": solver.wall_time,
        "response_stats": solver.response_stats(),
        "best_missing": min(max_missing, capture.best),
        "solver_returned_incumbent": bool(capture.records),
        "improvements": capture.records,
        "cover_found": any(r["missing"] == 0 for r in capture.records),
    }
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps({k: v for k, v in result.items() if k not in ("response_stats", "improvements")})
    )


if __name__ == "__main__":
    main()
