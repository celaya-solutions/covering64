# Document:    Point-essential regular cover search
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      3adc1999a004b57347fa7c9429e70f379665aa10132886ec4d66b980fb95c79b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Search the point-essential regular branch; complete only with degree19 branch.

If a point p in a selected block B occurs in no private triple of B, replacing
p by any point outside B preserves coverage and lowers its degree20 to19.
If that replacement is an existing block, simply deleting B gives a63-cover;
the degree lower bound19 then guarantees a degree19 point. Thus a cover of
size at most64 implies either a degree19 cover or a regular20 cover where
every block-point incidence is supported by a private triple. This is a
joint existence reduction, not a claim that every regular cover is essential.
"""

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

from covering64.core import Universe, read_blocks, verify_cover, write_blocks


def unsupported_incidences(blocks, t=3):
    counts = Counter(triple for block in blocks for triple in combinations(block, t))
    return [
        (index, point)
        for index, block in enumerate(blocks)
        for point in block
        if not any(point in triple and counts[triple] == 1 for triple in combinations(block, t))
    ]


def add_essential_constraints(universe, model, selected):
    private = [model.new_bool_var(f"private_{t}") for t in range(len(universe.triples))]
    for tid, ids in enumerate(universe.containing):
        count = sum(selected[i] for i in ids)
        model.add(count == 1).only_enforce_if(private[tid])
        model.add(count != 1).only_enforce_if(private[tid].Not())
    for bid, block in enumerate(universe.blocks):
        for point in block:
            model.add_bool_or(
                [selected[bid].Not()]
                + [private[tid] for tid in universe.coverage[bid] if point in universe.triples[tid]]
            )
    return private


def build_model(max_missing=0):
    if type(max_missing) is not int or max_missing < 0:
        raise ValueError("max_missing must be a nonnegative integer")
    universe = Universe.build()
    model = cp_model.CpModel()
    selected = [model.new_bool_var(f"block_{i}") for i in range(len(universe.blocks))]
    holes = [model.new_bool_var(f"hole_{i}") for i in range(len(universe.triples))]
    for tid, ids in enumerate(universe.containing):
        count = sum(selected[i] for i in ids)
        model.add(count == 0).only_enforce_if(holes[tid])
        model.add(count >= 1).only_enforce_if(holes[tid].Not())
    model.add(sum(holes) <= max_missing)
    model.add(sum(selected) == 64)
    # Relabel any chosen block to1..5; essentiality and degrees are invariant.
    model.add(selected[0] == 1)
    for point in range(1, 17):
        model.add(
            sum(selected[i] for i, block in enumerate(universe.blocks) if point in block) == 20
        )
    for pair in combinations(range(1, 17), 2):
        model.add(
            sum(selected[i] for i, block in enumerate(universe.blocks) if set(pair) <= set(block))
            >= 5
        )
    private = add_essential_constraints(universe, model, selected)
    # For M tracked triples with I incidences, h holes and u private triples,
    # I >= u +2*(M-h-u), hence u+2*h >=2*M-I. These are safe aggregates.
    model.add(sum(private) + 2 * sum(holes) >= 480)
    for point in range(1, 17):
        tids = [t for t, triple in enumerate(universe.triples) if point in triple]
        model.add(sum(private[t] + 2 * holes[t] for t in tids) >= 90)
    for pair in combinations(range(1, 17), 2):
        tids = [t for t, triple in enumerate(universe.triples) if set(pair) <= set(triple)]
        incidence = sum(
            selected[b] for b, block in enumerate(universe.blocks) if set(pair) <= set(block)
        )
        model.add(sum(private[t] + 2 * holes[t] for t in tids) + 3 * incidence >= 28)
    if max_missing:
        model.minimize(sum(holes))
    return universe, model, selected, holes, private


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=600)
    parser.add_argument("--seed", type=int, default=2026101400)
    parser.add_argument("--max-missing", type=int, default=0)
    parser.add_argument("--hint", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0 or args.seed < 0:
        parser.error("invalid time budget or seed")
    universe, model, selected, holes, private = build_model(args.max_missing)
    hint_mapping = None
    if args.hint:
        hint = read_blocks(args.hint)
        first = min(hint)
        order = list(first) + [p for p in range(1, 17) if p not in first]
        hint_mapping = dict(zip(order, range(1, 17)))
        transformed = {tuple(sorted(hint_mapping[p] for p in b)) for b in hint}
        for block, variable in zip(universe.blocks, selected):
            model.add_hint(variable, int(block in transformed))
        hint_counts = Counter(t for block in transformed for t in combinations(block, 3))
        for t, triple in enumerate(universe.triples):
            model.add_hint(holes[t], int(hint_counts[triple] == 0))
            model.add_hint(private[t], int(hint_counts[triple] == 1))
    args.output.mkdir(parents=True, exist_ok=True)
    model_path = args.output / "model.pbtxt"
    model.export_to_file(str(model_path))
    source = Path(__file__).read_bytes()
    (args.output / "source.py").write_bytes(source)
    metadata = {
        "scope": (
            "point-essential regular20 branch; joint completeness requires degree19 branch"
            if args.max_missing == 0
            else "partial-cover heuristic in point-essential regular20 family"
        ),
        "derivation": __doc__,
        "seed": args.seed,
        "seconds": args.seconds,
        "workers": 2,
        "max_missing": args.max_missing,
        "solver_version": ortools.__version__,
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "hint_sha256": hashlib.sha256(args.hint.read_bytes()).hexdigest() if args.hint else None,
        "hint_mapping": hint_mapping,
        "repair_hint": False,
        "private_count_aggregate_bounds": True,
        "complete_auxiliary_hint": bool(args.hint),
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = 2
    solver.parameters.random_seed = args.seed
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    with (args.output / "solver.log").open("w") as stream:
        solver.log_callback = lambda line: (stream.write(line + "\n"), stream.flush())
        status = solver.solve(model)
    result = {
        "status": solver.status_name(status),
        "seconds": solver.wall_time,
        "response_stats": solver.response_stats(),
        "proof_generated": False,
        "scope": metadata["scope"],
        "witness": None,
    }
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        blocks = [b for b, x in zip(universe.blocks, selected) if solver.value(x)]
        report = verify_cover(blocks)
        uncovered = len(report["uncovered"])
        if unsupported_incidences(blocks) or len(blocks) != 64 or uncovered > args.max_missing:
            raise RuntimeError("candidate violates essentiality, size or hole budget")
        if any(sum(point in b for b in blocks) != 20 for point in range(1, 17)):
            raise RuntimeError("candidate violates regularity")
        path = args.output / "candidate.txt"
        write_blocks(path, blocks)
        independent = subprocess.run(
            [sys.executable, "scripts/check_cover.py", str(path), "--expected-blocks", "64"],
            capture_output=True,
            text=True,
        )
        if independent.returncode not in (0, 1):
            raise RuntimeError(independent.stderr)
        independent = json.loads(independent.stdout)
        if independent["uncovered_count"] != uncovered or independent["valid"] != report["valid"]:
            raise RuntimeError("cover checkers disagree")
        result.update(witness=blocks, uncovered=uncovered, package=report, independent=independent)
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
