# Document:    Native SAT search for point-essential regular covers
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Point-essential regular20 search; complete only jointly with degree19 cases."""

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import math
import subprocess
import sys
import threading
import time
from pathlib import Path

from native_sat_search import make_solver, native_model
from pysat.card import CardEnc, EncType

from covering64.core import Universe, verify_cover, write_blocks


def add_essential_native(universe, model):
    """Extend a full-cover native model with guarded exact-one equivalences.

    Public block variables remain1..N. A private flag uses two disjoint
    sequential-counter encodings: true requires at most1 incident block;
    false requires at least2. Coverage is explicit, so the flag is equivalent
    to multiplicity1. All auxiliary IDs exceed every private flag.
    """
    n = len(universe.blocks)
    private = [n + t + 1 for t in range(len(universe.triples))]
    top = n + len(private)
    for tid, containing in enumerate(universe.containing):
        ids = [bid + 1 for bid in containing]
        flag = private[tid]
        model["clauses"].append(ids)
        if len(ids) <= 1:
            model["clauses"].append([flag if ids else -flag])
            continue
        at_most = CardEnc.atmost(ids, bound=1, top_id=top, encoding=EncType.seqcounter)
        top = max(top, at_most.nv)
        model["clauses"].extend([[-flag] + clause for clause in at_most.clauses])
        at_least = CardEnc.atleast(ids, bound=2, top_id=top, encoding=EncType.seqcounter)
        top = max(top, at_least.nv)
        model["clauses"].extend([[flag] + clause for clause in at_least.clauses])
    for bid, block in enumerate(universe.blocks):
        for point in block:
            model["clauses"].append(
                [-bid - 1]
                + [private[t] for t in universe.coverage[bid] if point in universe.triples[t]]
            )
    model["variables"] = top
    return private


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=600)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("seconds must be finite and positive")
    universe = Universe.build()
    model = native_model(universe, 64, branch="regular20", normalize=True)
    add_essential_native(universe, model)
    args.output.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(model, separators=(",", ":")).encode()
    (args.output / "model.json.gz").write_bytes(gzip.compress(serialized, mtime=0))
    sources = {}
    for name in ["essential_native_search.py", "native_sat_search.py"]:
        raw = Path(__file__).with_name(name).read_bytes()
        sources[name] = hashlib.sha256(raw).hexdigest()
        (args.output / name).write_bytes(raw)
    metadata = {
        "scope": __doc__,
        "seconds": args.seconds,
        "workers": 1,
        "seed_policy": "Minicard default; no randomized hint",
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "sources": sources,
        "model_sha256": hashlib.sha256(serialized).hexdigest(),
        "python_sat_version": importlib.metadata.version("python-sat"),
        "variables": model["variables"],
        "clauses": len(model["clauses"]),
        "atmost_constraints": len(model["atmost"]),
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    solver = make_solver(model)
    timer = threading.Timer(args.seconds, solver.interrupt)
    started = time.monotonic()
    timer.start()
    try:
        answer = solver.solve_limited(expect_interrupt=True)
        result = {
            "status": "UNKNOWN" if answer is None else "SAT" if answer else "UNSAT",
            "elapsed_seconds": time.monotonic() - started,
            "statistics": solver.accum_stats(),
            "proof_generated": False,
            "scope": __doc__,
            "witness": None,
        }
        if answer:
            true = {lit for lit in solver.get_model() if lit > 0}
            blocks = [b for i, b in enumerate(universe.blocks, 1) if i in true]
            checked = verify_cover(blocks)
            if not checked["valid"] or len(blocks) != 64:
                raise RuntimeError("SAT candidate failed package verification")
            path = args.output / "cover.txt"
            write_blocks(path, blocks)
            independent = json.loads(
                subprocess.check_output(
                    [
                        sys.executable,
                        "scripts/check_cover.py",
                        str(path),
                        "--expected-blocks",
                        "64",
                    ],
                    text=True,
                )
            )
            result.update(witness=blocks, package=checked, independent=independent)
    finally:
        timer.cancel()
        solver.delete()
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
