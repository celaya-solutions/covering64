# Document:    Covering search with necessary link bounds
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Full-universe feasibility with proved pair/point bounds and degree ordering.

Each pair needs at least ceil(14/3)=5 blocks to cover its fourteen third points.
For a point, 4*r counts pair incidences, hence 4*r >= 15*5 and r >= 19.
Ordering point degrees preserves existence by relabeling any witness in degree
order. No first-block constraint is added, so the two normalizations cannot clash.
"""

import argparse
import hashlib
import json
import platform
import subprocess
import time
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import Universe, verify_cover, write_blocks


def build_link_model(universe, target=64, order_degrees=True):
    if (universe.v, universe.k, universe.t) != (16, 5, 3):
        raise ValueError("Link bounds here are proved only for (16,5,3)")
    model = cp_model.CpModel()
    selected = [model.new_bool_var(f"block_{i + 1}") for i in range(len(universe.blocks))]
    for containing in universe.containing:
        model.add_bool_or([selected[i] for i in containing])
    model.add(sum(selected) == target)
    pairs = {pair: [] for pair in combinations(range(1, 17), 2)}
    points = {point: [] for point in range(1, 17)}
    for block, var in zip(universe.blocks, selected):
        for pair in combinations(block, 2):
            pairs[pair].append(var)
        for point in block:
            points[point].append(var)
    for variables in pairs.values():
        model.add(sum(variables) >= 5)
    degrees = []
    for point, variables in points.items():
        degree = model.new_int_var(19, target, f"replication_{point}")
        model.add(degree == sum(variables))
        degrees.append(degree)
    if order_degrees:
        for previous, following in zip(degrees, degrees[1:]):
            model.add(previous <= following)
    return model, selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=300)
    parser.add_argument("--seed", type=int, default=2026100307)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--target", type=int, default=64)
    parser.add_argument("--unordered", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    universe = Universe.build()
    model, selected = build_link_model(universe, args.target, not args.unordered)
    source = Path(__file__).read_bytes()
    (args.output / "source.py").write_bytes(source)
    model.export_to_file(str(args.output / "model.pbtxt"))
    settings = {
        "scope": "full universe; safe degree ordering by point relabeling",
        "seconds": args.seconds, "seed": args.seed, "workers": args.workers,
        "target": args.target, "degree_ordered": not args.unordered,
        "pair_lower_bound": 5, "point_lower_bound": 19,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                   text=True).strip(),
        "solver_version": ortools.__version__, "platform": platform.platform(),
        "model_sha256": hashlib.sha256((args.output / "model.pbtxt").read_bytes()).hexdigest(),
    }
    (args.output / "settings.json").write_text(json.dumps(settings, indent=2) + "\n")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.random_seed = args.seed
    solver.parameters.num_search_workers = args.workers
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    started = time.monotonic()
    with (args.output / "solver.log").open("w") as log:
        solver.log_callback = lambda message: log.write(message + "\n")
        status = solver.solve(model)
    result = {**settings, "status": solver.status_name(status),
              "elapsed_seconds": time.monotonic() - started,
              "response_stats": solver.response_stats(), "proof_generated": False}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        witness = [b for b, x in zip(universe.blocks, selected) if solver.value(x)]
        result["verification"] = verify_cover(witness)
        if not result["verification"]["valid"] or len(witness) != args.target:
            raise RuntimeError("Candidate failed package verification")
        write_blocks(args.output / "witness.txt", witness)
        for name, command in (
            ("package", ["uv", "run", "covering64", "verify"]),
            ("independent", ["uv", "run", "python", "scripts/check_cover.py"]),
        ):
            check = subprocess.run(command + [str(args.output / "witness.txt"),
                                   "--expected-blocks", str(args.target)],
                                   capture_output=True, text=True, check=True)
            (args.output / f"{name}-verification.json").write_text(check.stdout)
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "elapsed_seconds": result["elapsed_seconds"]}))


if __name__ == "__main__":
    main()
