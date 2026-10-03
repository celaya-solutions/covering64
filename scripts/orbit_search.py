# Document:    Restricted orbit covering search
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Search explicitly restricted permutation-invariant covering families."""

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import Universe, verify_cover, write_blocks


def cyclic_permutation(lengths, v=16):
    """Disjoint cycles followed by fixed points; labels remain one-based."""
    if any(n < 1 for n in lengths) or sum(lengths) > v:
        raise ValueError("Invalid disjoint cycle lengths")
    result = list(range(1, v + 1))
    start = 0
    for length in lengths:
        for j in range(length):
            result[start + j] = start + (j + 1) % length + 1
        start += length
    return tuple(result)


def block_orbits(universe, generators):
    """Partition the complete lexicographic block universe under generators."""
    for generator in generators:
        if sorted(generator) != list(range(1, universe.v + 1)):
            raise ValueError("A generator must permute every point")
    lookup = {block: i for i, block in enumerate(universe.blocks)}
    unseen = set(range(len(universe.blocks)))
    orbits = []
    while unseen:
        seed = min(unseen)
        orbit = {seed}
        queue = [seed]
        while queue:
            index = queue.pop()
            for generator in generators:
                block = tuple(sorted(generator[p - 1] for p in universe.blocks[index]))
                other = lookup[block]
                if other not in orbit:
                    orbit.add(other)
                    queue.append(other)
        unseen.difference_update(orbit)
        orbits.append(tuple(sorted(orbit)))
    return tuple(orbits)


def search(universe, generators, target, seconds, seed, workers):
    orbits = block_orbits(universe, generators)
    orbit_of = {b: i for i, orbit in enumerate(orbits) for b in orbit}
    model = cp_model.CpModel()
    selected = [model.new_bool_var(f"orbit_{i}") for i in range(len(orbits))]
    for containing in universe.containing:
        model.add_bool_or([selected[i] for i in sorted({orbit_of[b] for b in containing})])
    model.add(sum(len(o) * x for o, x in zip(orbits, selected)) <= target)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.random_seed = seed
    solver.parameters.num_search_workers = workers
    status = solver.solve(model)
    result = {
        "scope": "Only covers invariant under the listed generators; not unrestricted",
        "generators": generators,
        "target": target,
        "seed": seed,
        "seconds_budget": seconds,
        "workers": workers,
        "orbit_count": len(orbits),
        "orbit_sizes": sorted({len(o) for o in orbits}),
        "status": solver.status_name(status),
        "response_stats": solver.response_stats(),
        "solver_version": ortools.__version__,
        "python_version": platform.python_version(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "proof_generated": False,
        "witness": None,
    }
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        ids = sorted(b for o, x in zip(orbits, selected) if solver.value(x) for b in o)
        witness = [universe.blocks[b] for b in ids]
        result["verification"] = verify_cover(witness, universe.v, universe.k, universe.t)
        if not result["verification"]["valid"] or len(witness) > target:
            raise RuntimeError("Invalid orbit search witness")
        result["witness"] = witness
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles", type=int, nargs="*", default=[])
    parser.add_argument("--translations", action="store_true")
    parser.add_argument("--target", type=int, default=64)
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    generators = [cyclic_permutation(args.cycles)]
    if args.translations:
        generators = [tuple((p ^ bit) + 1 for p in range(16)) for bit in (1, 2, 4, 8)]
    result = search(Universe.build(), generators, args.target, args.seconds,
                    args.seed, args.workers)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    if result["witness"]:
        witness_path = args.output.with_suffix(".txt")
        write_blocks(witness_path, result["witness"])
        count = len(result["witness"])
        for command in (
            ["uv", "run", "covering64", "verify"],
            ["uv", "run", "python", "scripts/check_cover.py"],
        ):
            subprocess.run(command + [str(witness_path), "--expected-blocks", str(count)],
                           check=True)
    print(json.dumps({k: result[k] for k in ("status", "orbit_count", "orbit_sizes")}))


if __name__ == "__main__":
    main()
