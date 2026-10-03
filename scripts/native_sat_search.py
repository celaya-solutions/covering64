#!/usr/bin/env python3
# Document:    Native Cardinality SAT Cover Search
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Unrestricted Minicard feasibility search; UNSAT needs a separate checked proof."""

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import math
import random
import subprocess
import sys
import threading
import time
from itertools import combinations
from pathlib import Path

from pysat.solvers import Minicard

from covering64.core import (
    Universe,
    normalize_blocks,
    read_blocks,
    schonheim_bound,
    verify_cover,
    write_blocks,
)


def native_model(universe, target):
    """Return coverage clauses and native at-most constraints in public ID order.

    Every k-block has its own variable, with no symmetry or incumbent restriction.
    A cover's s-subset link covers all (t-s)-subsets on the other v-s points;
    hence its incidence meets the recursive Schonheim bound. Negating all link
    literals turns the necessary lower bound into a native at-most constraint.
    """
    if type(target) is not int or target < 0:
        raise ValueError("target must be a nonnegative integer")
    clauses = [[i + 1 for i in containing] for containing in universe.containing]
    atmost = [(list(range(1, len(universe.blocks) + 1)), target)]
    block_sets = [set(block) for block in universe.blocks]
    for size in range(1, universe.t):
        bound = schonheim_bound(universe.v - size, universe.k - size, universe.t - size)
        for subset in combinations(range(1, universe.v + 1), size):
            required = set(subset)
            incident = [i + 1 for i, block in enumerate(block_sets) if required <= block]
            atmost.append(([-i for i in incident], len(incident) - bound))
    return {"variables": len(universe.blocks), "clauses": clauses, "atmost": atmost}


def make_solver(model):
    solver = Minicard(bootstrap_with=model["clauses"])
    for literals, limit in model["atmost"]:
        solver.add_atmost(literals, limit)
    return solver


def hint_phases(universe, blocks, seed):
    normalized = normalize_blocks(blocks, universe.v, universe.k)
    labels = list(range(1, universe.v + 1))
    if seed:
        random.Random(seed).shuffle(labels)
    mapping = dict(zip(range(1, universe.v + 1), labels))
    selected = {tuple(sorted(mapping[x] for x in block)) for block in normalized}
    phases = [i + 1 if block in selected else -i - 1 for i, block in enumerate(universe.blocks)]
    return phases, mapping


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target", type=int, default=64)
    parser.add_argument("--seconds", type=float, default=600)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--hint", type=Path)
    args = parser.parse_args(argv)
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("seconds must be finite and positive")
    universe = Universe.build()
    model = native_model(universe, args.target)
    serialized = json.dumps(model, separators=(",", ":")).encode()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "model.json.gz").write_bytes(gzip.compress(serialized, mtime=0))
    (args.output / "source_snapshot.py").write_bytes(Path(__file__).read_bytes())
    solver = make_solver(model)
    mapping = None
    if args.hint:
        phases, mapping = hint_phases(universe, read_blocks(args.hint), args.seed)
        solver.set_phases(phases)
    metadata = {
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "model_sha256": hashlib.sha256(serialized).hexdigest(),
        "solver": "PySAT Minicard", "python_sat_version": importlib.metadata.version("python-sat"),
        "workers": 1, "target": args.target, "seconds": args.seconds, "seed": args.seed,
        "seed_scope": "hint label permutation only; solver default random policy unchanged",
        "hint_permutation": mapping,
        "hint_sha256": hashlib.sha256(args.hint.read_bytes()).hexdigest() if args.hint else None,
        "scope": "unrestricted block family with safe link bounds; no independently checked proof",
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    started = time.monotonic()
    timer = threading.Timer(args.seconds, solver.interrupt)
    timer.start()
    try:
        status = solver.solve_limited(expect_interrupt=True)
    finally:
        timer.cancel()
    result = {
        "status": "SAT" if status is True else "UNSAT_UNCHECKED" if status is False else "UNKNOWN",
        "elapsed_seconds": time.monotonic() - started, "statistics": solver.accum_stats(),
        "scope": metadata["scope"], "witness": None,
    }
    if status is True:
        assignment = set(solver.get_model())
        witness = [block for i, block in enumerate(universe.blocks) if i + 1 in assignment]
        checked = verify_cover(witness)
        if not checked["valid"] or len(witness) > args.target:
            raise RuntimeError("SAT candidate failed full package verification")
        path = args.output / "cover.txt"
        write_blocks(path, witness)
        run = subprocess.run([sys.executable, "scripts/check_cover.py", str(path)],
                             capture_output=True, text=True, check=True)
        independent = json.loads(run.stdout)
        if not independent["valid"]:
            raise RuntimeError("standalone verification rejected SAT candidate")
        result.update(witness=witness, verification=checked, standalone_verification=independent)
    solver.delete()
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
