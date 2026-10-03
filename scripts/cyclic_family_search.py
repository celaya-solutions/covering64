# Document:    Restricted cyclic family search with incidence bounds
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Bounded searches in explicit permutation-invariant families; no global claim."""

import argparse
import hashlib
import json
import platform
import subprocess
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

import ortools
from orbit_search import block_orbits, cyclic_permutation
from ortools.sat.python import cp_model

from covering64.core import Universe, read_blocks, verify_cover, write_blocks


def build_model(universe, generators, target, hint=()):
    """Retain whole block orbits and impose only necessary incidence bounds.

    Every pair lies in at least ceil(14/3)=5 blocks. Thus each point lies
    in at least ceil(15*5/4)=19 blocks, and there are at least61 blocks.
    The family restriction is explicit; these bounds do not require regularity.
    """
    if type(target) is not int or target < 0:
        raise ValueError("target must be a nonnegative integer")
    orbits = block_orbits(universe, generators)
    orbit_of = {bid: oid for oid, orbit in enumerate(orbits) for bid in orbit}
    model = cp_model.CpModel()
    xs = [model.new_bool_var(f"orbit_{i}") for i in range(len(orbits))]
    size = sum(len(orbit) * x for orbit, x in zip(orbits, xs))
    model.add(size <= target)
    model.add(size >= 61)
    for ids in universe.containing:
        model.add_bool_or([xs[oid] for oid in sorted({orbit_of[b] for b in ids})])
    point_coefficients = [Counter() for _ in range(16)]
    pair_coefficients = {pair: Counter() for pair in combinations(range(1, 17), 2)}
    for bid, block in enumerate(universe.blocks):
        oid = orbit_of[bid]
        for point in block:
            point_coefficients[point - 1][oid] += 1
        for pair in combinations(block, 2):
            pair_coefficients[pair][oid] += 1
    for coefs in point_coefficients:
        model.add(sum(coef * xs[oid] for oid, coef in coefs.items()) >= 19)
    for coefs in pair_coefficients.values():
        model.add(sum(coef * xs[oid] for oid, coef in coefs.items()) >= 5)
    if hint:
        selected = set(hint)
        for orbit, x in zip(orbits, xs):
            model.add_hint(x, int(all(universe.blocks[b] in selected for b in orbit)))
    return model, xs, orbits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles", type=int, nargs="*", default=[])
    parser.add_argument("--target", type=int, default=64)
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--hint", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.seconds <= 0 or args.workers < 1 or args.seed < 0:
        parser.error("positive time/workers and nonnegative seed required")
    universe = Universe.build()
    generators = [cyclic_permutation(args.cycles)]
    hint = read_blocks(args.hint) if args.hint else ()
    model, xs, orbits = build_model(universe, generators, args.target, hint)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    model_path = args.output.with_suffix(".pbtxt")
    model.export_to_file(str(model_path))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = args.seed
    start = time.monotonic()
    status = solver.solve(model)
    elapsed = time.monotonic() - start
    result = {
        "scope": "Only covers invariant under explicit generators; no global claim",
        "generators": generators,
        "cycles": args.cycles,
        "target": args.target,
        "seconds_budget": args.seconds,
        "workers": args.workers,
        "seed": args.seed,
        "status": solver.status_name(status),
        "elapsed_seconds": elapsed,
        "response_stats": solver.response_stats(),
        "solver_version": ortools.__version__,
        "python_version": platform.python_version(),
        "orbit_count": len(orbits),
        "orbit_size_counts": dict(Counter(map(len, orbits))),
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "orbit_source_sha256": hashlib.sha256(
            Path(__file__).with_name("orbit_search.py").read_bytes()
        ).hexdigest(),
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "proof_generated": False,
        "witness": None,
    }
    if args.hint:
        result["hint_sha256"] = hashlib.sha256(args.hint.read_bytes()).hexdigest()
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        blocks = sorted(
            universe.blocks[b] for orbit, x in zip(orbits, xs) if solver.value(x) for b in orbit
        )
        report = verify_cover(blocks)
        if not report["valid"] or len(blocks) > args.target:
            raise RuntimeError("solver witness failed package verification")
        witness = args.output.with_suffix(".txt")
        write_blocks(witness, blocks)
        result["witness"] = blocks
        result["package_verification"] = report
        result["standalone_verification"] = json.loads(
            subprocess.check_output(
                [
                    "uv",
                    "run",
                    "python",
                    "scripts/check_cover.py",
                    str(witness),
                    "--expected-blocks",
                    str(len(blocks)),
                ],
                text=True,
            )
        )
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps({k: result[k] for k in ("cycles", "status", "elapsed_seconds", "orbit_count")})
    )


if __name__ == "__main__":
    main()
