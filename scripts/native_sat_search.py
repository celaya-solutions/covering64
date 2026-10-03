#!/usr/bin/env python3
# Document:    Native Cardinality SAT Cover Search
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Minicard search with optional complete degree branches; UNSAT needs a checked proof."""

import argparse
import gzip
import hashlib
import importlib.metadata
import importlib.util
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


def native_model(universe, target, branch=None, normalize=False):
    """Return coverage clauses and native at-most constraints in public ID order.

    Every k-block has its own variable. The default model has no symmetry or
    incumbent restriction; optional degree branches and their normalizations
    preserve existence across the complete two-branch split.
    A cover's s-subset link covers all (t-s)-subsets on the other v-s points;
    hence its incidence meets the recursive Schonheim bound. Negating all link
    literals turns the necessary lower bound into a native at-most constraint.
    """
    if type(target) is not int or target < 0:
        raise ValueError("target must be a nonnegative integer")
    if branch not in (None, "regular20", "degree19"):
        raise ValueError("invalid degree branch")
    if branch and (universe.v, universe.k, universe.t) != (16, 5, 3):
        raise ValueError("degree branches only apply to C(16,5,3)")
    if normalize and branch is None:
        raise ValueError("normalization requires a degree branch")
    clauses = [[i + 1 for i in containing] for containing in universe.containing]
    atmost = [(list(range(1, len(universe.blocks) + 1)), target)]
    block_sets = [set(block) for block in universe.blocks]
    for size in range(1, universe.t):
        bound = schonheim_bound(universe.v - size, universe.k - size, universe.t - size)
        for subset in combinations(range(1, universe.v + 1), size):
            required = set(subset)
            incident = [i + 1 for i, block in enumerate(block_sets) if required <= block]
            atmost.append(([-i for i in incident], len(incident) - bound))
    if branch == "regular20":
        atmost.append((list(range(-1, -len(universe.blocks) - 1, -1)), len(universe.blocks) - 64))
        for point in range(1, 17):
            incident = [i + 1 for i, block in enumerate(universe.blocks) if point in block]
            atmost.append((incident, 20))
            atmost.append(([-i for i in incident], len(incident) - 20))
    elif branch == "degree19":
        incident = [i + 1 for i, block in enumerate(universe.blocks) if 1 in block]
        atmost.append((incident, 19))  # Existing safe lower bound supplies equality.
        excess = {(2, x) for x in range(3, 7)} | {(x, x + 1) for x in range(7, 17, 2)}
        for triple, containing in zip(universe.triples, universe.containing):
            if triple[0] != 1:
                continue
            literals = [i + 1 for i in containing]
            count = 2 if triple[1:] in excess else 1
            atmost.append((literals, count))
            if count == 2:
                atmost.append(([-i for i in literals], len(literals) - 2))
    if normalize:
        if branch == "regular20":
            clauses.append([1])
        else:
            representatives = [(1, 2, 7, 8, 9), (1, 2, 7, 9, 11),
                               (1, 2, 3, 7, 8), (1, 2, 3, 7, 9)]
            clauses.append([universe.blocks.index(block) + 1 for block in representatives])
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
    parser.add_argument("--branch", choices=["regular20", "degree19"])
    parser.add_argument("--normalize", action="store_true")
    parser.add_argument("--core-proof", type=Path)
    args = parser.parse_args(argv)
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("seconds must be finite and positive")
    if args.core_proof and args.target > 64:
        parser.error("the core proof only supports target<=64")
    universe = Universe.build()
    model = native_model(universe, args.target, args.branch, args.normalize)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "source_snapshot.py").write_bytes(Path(__file__).read_bytes())
    solver = make_solver(model)
    mapping = None
    canonical_mapping = None
    if args.hint:
        hint = read_blocks(args.hint)
        if args.branch == "degree19" or args.normalize:
            path = Path(__file__).with_name("degree_split_search.py")
            spec = importlib.util.spec_from_file_location("native_degree_split", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if args.normalize:
                hint, canonical_mapping = module.normalize_split_hint(hint, args.branch)
            else:
                hint, canonical_mapping = module.canonicalize_degree19_hint(hint)
            if args.seed:
                parser.error("normalized hints require seed0 to preserve their pattern")
            (args.output / "degree_split_source_snapshot.py").write_bytes(path.read_bytes())
        phases, mapping = hint_phases(universe, hint, args.seed)
        solver.set_phases(phases)
    core_cut = None
    if args.core_proof:
        helper = Path(__file__).with_name("checked_core_cut.py")
        spec = importlib.util.spec_from_file_location("native_checked_core", helper)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        core_mapping = canonical_mapping if canonical_mapping is not None else mapping
        core_cut = module.checked_core_cuts(universe, args.core_proof, core_mapping)
        for cut in core_cut["cuts"]:
            literals = [i + 1 for i in cut["block_ids"]]
            model["atmost"].append((literals, cut["limit"]))
            solver.add_atmost(literals, cut["limit"])
        (args.output / "core_cut_source_snapshot.py").write_bytes(helper.read_bytes())
        (args.output / "core_checker_snapshot.py").write_bytes(
            Path(core_cut["checker_path"]).read_bytes())
        (args.output / "core_proof_check.json").write_text(json.dumps(core_cut, indent=2) + "\n")
    serialized = json.dumps(model, separators=(",", ":")).encode()
    (args.output / "model.json.gz").write_bytes(gzip.compress(serialized, mtime=0))
    metadata = {
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "model_sha256": hashlib.sha256(serialized).hexdigest(),
        "solver": "PySAT Minicard", "python_sat_version": importlib.metadata.version("python-sat"),
        "workers": 1, "target": args.target, "seconds": args.seconds, "seed": args.seed,
        "branch": args.branch, "canonical_hint_permutation": canonical_mapping,
        "normalize": args.normalize,
        "core_cut": core_cut,
        "seed_scope": "hint label permutation only; solver default random policy unchanged",
        "hint_permutation": mapping,
        "hint_sha256": hashlib.sha256(args.hint.read_bytes()).hexdigest() if args.hint else None,
        "scope": ("unrestricted block family" if args.branch is None else
                  "one of two complete <=64 degree branches")
                 + "; no independently checked proof",
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
