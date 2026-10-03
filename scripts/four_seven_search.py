# Document:    Four Sevenfold Triple Branch Search
# Version:     v1.2.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      790dee9054603155be084152c74649dd22ecef7a99dce7236224386680a4d2dd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Search the two checked regular four-sevenfold-triple branches."""

from __future__ import annotations

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
from ortools.sat.python import cp_model

from covering64.core import Universe, verify_cover, write_blocks

ANCHORS = tuple(tuple(range(4 * i + 1, 4 * i + 4)) for i in range(4))
HUBS = (4, 8, 12, 16)


def pair_targets(case):
    """All pair counts forced by this full-cover branch, without extra symmetry."""
    if case not in ("cycle", "matching"):
        raise ValueError("case must be cycle or matching")
    targets = {pair: 5 for pair in combinations(range(1, 17), 2)}
    for anchors, hub in zip(ANCHORS, HUBS):
        for pair in combinations(anchors, 2):
            targets[pair] = 7
        for anchor in anchors:
            targets[tuple(sorted((anchor, hub)))] = 6
    edges = ((4, 8), (8, 12), (12, 16), (4, 16))
    if case == "matching":
        edges = ((4, 8), (12, 16))
    for edge in edges:
        targets[edge] += 1 if case == "cycle" else 2
    return targets


def allowed_block(block):
    return all(len(set(block).intersection(anchors)) != 2 for anchors in ANCHORS)


def group_generators(case):
    """Optional construction restrictions, NOT complete symmetry reductions."""
    pair_targets(case)
    shifts = (1,) if case == "cycle" else (1, 2)
    return [
        tuple(
            4 * (((p // 4 + shift) % 4) if case == "cycle" else ((p // 4) ^ shift))
            + p % 4 + 1
            for p in range(16)
        )
        for shift in shifts
    ]


def add_group_symmetry(model, xs, universe, case):
    generators = group_generators(case)
    indices = {b: i for i, b in enumerate(universe.blocks)}
    remaining = set(range(len(xs)))
    sizes = Counter()
    allowed_orbits = 0
    while remaining:
        root = min(remaining)
        orbit = {root}
        queue = [root]
        while queue:
            i = queue.pop()
            for generator in generators:
                j = indices[tuple(sorted(generator[p - 1] for p in universe.blocks[i]))]
                if j not in orbit:
                    orbit.add(j)
                    queue.append(j)
        for i in sorted(orbit - {root}):
            model.add(xs[i] == xs[root])
        remaining.difference_update(orbit)
        sizes[len(orbit)] += 1
        allowed_orbits += allowed_block(universe.blocks[root])
    return {"generators": generators, "orbit_sizes": dict(sizes), "allowed_orbits": allowed_orbits}


def build_model(case, max_missing=0):
    if type(max_missing) is not int or not 0 <= max_missing <= 560:
        raise ValueError("max_missing must be an integer in 0..560")
    targets = pair_targets(case)
    universe = Universe.build()
    model = cp_model.CpModel()
    xs = [model.new_bool_var(f"block_{i}") for i in range(len(universe.blocks))]
    holes = []
    allowed = [i for i, block in enumerate(universe.blocks) if allowed_block(block)]
    allowed_set = set(allowed)
    for i, x in enumerate(xs):
        if i not in allowed_set:
            model.add(x == 0)
    model.add(sum(xs) == 64)
    for point in range(1, 17):
        model.add(sum(xs[i] for i in allowed if point in universe.blocks[i]) == 20)
    for pair, target in targets.items():
        model.add(
            sum(xs[i] for i in allowed if set(pair).issubset(universe.blocks[i])) == target
        )
    for anchors in ANCHORS:
        model.add(
            sum(xs[i] for i in allowed if set(anchors).issubset(universe.blocks[i])) == 7
        )
    for tid, ids in enumerate(universe.containing):
        count = sum(xs[i] for i in ids if i in allowed_set)
        if max_missing:
            hole = model.new_bool_var(f"hole_{tid}")
            holes.append(hole)
            model.add(count == 0).only_enforce_if(hole)
            model.add(count >= 1).only_enforce_if(hole.Not())
        else:
            model.add(count >= 1)
    if max_missing:
        model.add(sum(holes) <= max_missing)
        model.minimize(sum(holes))
    return universe, model, xs, holes


def check_candidate(blocks, case):
    """Check branch constraints directly, apart from model and solver internals."""
    result = verify_cover(blocks)
    if result["blocks"] != 64:
        raise ValueError("candidate must have exactly 64 distinct blocks")
    if Counter(p for block in blocks for p in block) != Counter(dict.fromkeys(range(1, 17), 20)):
        raise ValueError("candidate is not regular")
    if Counter(pair for block in blocks for pair in combinations(block, 2)) != pair_targets(case):
        raise ValueError("candidate does not have branch pair multiplicities")
    counts = Counter(t for block in blocks for t in combinations(block, 3))
    if any(counts[t] != 7 for t in ANCHORS) or not all(map(allowed_block, blocks)):
        raise ValueError("candidate fails anchor constraints")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=("cycle", "matching"))
    parser.add_argument("--seconds", type=float, default=300)
    parser.add_argument("--seed", type=int, default=2026100401)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-missing", type=int, default=0)
    parser.add_argument("--group-symmetry", action="store_true",
                        help="Restrict constructions to a specified order-four group; incomplete")
    parser.add_argument("--double-cuts", action="store_true",
                        help="Track the400 possible nonfixed doubled triples explicitly")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (
        not math.isfinite(args.seconds)
        or args.seconds <= 0
        or args.workers < 1
        or not 0 <= args.max_missing <= 560
        or not 0 <= args.seed < 2**31
    ):
        parser.error("invalid search parameters")
    if args.double_cuts and args.max_missing:
        parser.error("double cuts require full unconditional triple coverage")
    if args.output.exists():
        parser.error("output directory must be new")
    args.output.mkdir(parents=True)
    universe, model, xs, holes = build_model(args.case, args.max_missing)
    symmetry = add_group_symmetry(model, xs, universe, args.case) if args.group_symmetry else None
    double_application = None
    double_source = None
    if args.double_cuts:
        from four_seven_double_cuts import add_double_triple_cuts

        _, double_application = add_double_triple_cuts(universe, model, xs, args.case)
        double_source = Path(__file__).with_name("four_seven_double_cuts.py").read_bytes()
        (args.output / "four_seven_double_cuts.py").write_bytes(double_source)
    source = Path(__file__).read_bytes()
    (args.output / "source.py").write_bytes(source)
    model_path = args.output / "model.pbtxt"
    model.export_to_file(str(model_path))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = args.seed
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    metadata = {
        "case": args.case,
        "scope": "Regular 64-block covers with four sevenfold triples only. "
        "Partial search retains full-cover branch constraints. "
        "UNKNOWN is inconclusive; INFEASIBLE is not an independently checked theorem.",
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "solver_version": ortools.__version__,
        "parameters": str(solver.parameters),
        "seconds": args.seconds,
        "seed": args.seed,
        "workers": args.workers,
        "max_missing": args.max_missing,
        "group_symmetry": symmetry,
        "double_cuts": double_application,
        "double_source_sha256": (
            hashlib.sha256(double_source).hexdigest() if double_source else None
        ),
        "variables": len(model.proto.variables),
        "constraints": len(model.proto.constraints),
        "allowed_blocks": sum(map(allowed_block, universe.blocks)),
    }
    if symmetry:
        metadata["scope"] += " Further restricted to the recorded order-four group action; " \
            "this construction subcase does not exhaust the four-sevenfold branch."
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    with (args.output / "solver.log").open("w") as log:
        solver.log_callback = lambda line: (log.write(line + "\n"), log.flush())
        status = solver.solve(model)
    result = {
        "status": solver.status_name(status),
        "seconds": solver.wall_time,
        "response_stats": solver.response_stats(),
        "cover_found": False,
    }
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        blocks = [block for i, block in enumerate(universe.blocks) if solver.value(xs[i])]
        package = check_candidate(blocks, args.case)
        if symmetry and any(
            {tuple(sorted(g[p - 1] for p in b)) for b in blocks} != set(blocks)
            for g in symmetry["generators"]
        ):
            raise RuntimeError("candidate does not obey requested symmetry")
        candidate = args.output / "candidate.txt"
        write_blocks(candidate, blocks)
        proc = subprocess.run(
            [sys.executable, "scripts/check_cover.py", str(candidate), "--expected-blocks", "64"],
            capture_output=True, text=True, check=False,
        )
        if proc.returncode not in (0, 1):
            raise RuntimeError(proc.stderr)
        standalone = json.loads(proc.stdout)
        if (
            standalone["uncovered_count"] != len(package["uncovered"])
            or standalone["valid"] != package["valid"]
            or (holes and sum(solver.value(h) for h in holes) != len(package["uncovered"]))
        ):
            raise RuntimeError("candidate verification mismatch")
        result.update(package=package, standalone=standalone, cover_found=standalone["valid"])
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("response_stats", "package")}))


if __name__ == "__main__":
    main()
