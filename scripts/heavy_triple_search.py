# Document:    Regular Multiplicity-Seven Triple Search
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      70e69116e1a24ec1bb7d1457c1b9087328cf3d8cc71bb03382412e9bcc726373
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Search the normalized regular64 branch containing a sevenfold triple.

The full-cover counting reduction is proved in the heavy-triple research note.
Positive-hole optimization is a restricted construction search only.
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
from essential_regular_search import build_model, unsupported_incidences
from ortools.sat.python import cp_model

from covering64.core import verify_cover, write_blocks

FIXED = [(1, 2, 3, 4, 5), (1, 2, 3, 4, 6)] + [(1, 2, 3, a, a + 1) for a in range(7, 16, 2)]


def add_heavy_count_cuts(universe, model, xs):
    """Full regular-cover consequences; a restriction when holes are allowed."""
    six_plus = []
    sevens = []
    for tid, ids in enumerate(universe.containing):
        count = sum(xs[i] for i in ids)
        model.add(count <= 7)
        high = model.new_bool_var(f"heavy6_{tid}")
        seven = model.new_bool_var(f"heavy7_{tid}")
        model.add(count >= 6).only_enforce_if(high)
        model.add(count <= 5).only_enforce_if(high.Not())
        model.add(count == 7).only_enforce_if(seven)
        model.add(count <= 6).only_enforce_if(seven.Not())
        six_plus.append(high)
        sevens.append(seven)
    for point in range(1, 17):
        model.add(
            sum(six_plus[t] for t, triple in enumerate(universe.triples) if point in triple) <= 1
        )
    model.add(3 * sum(six_plus) + sum(sevens) <= 16)


def build_heavy_model(max_missing=0, count_cuts=False):
    universe, model, xs, holes, private = build_model(max_missing)
    rank = {b: i for i, b in enumerate(universe.blocks)}
    fixed_ids = [rank[b] for b in FIXED]
    for bid in fixed_ids:
        model.add(xs[bid] == 1)
    for a in (1, 2, 3):
        for q in range(a + 1, 17):
            target = 7 if q <= 3 else 6 if q == 4 else 5
            model.add(
                sum(xs[i] for i, b in enumerate(universe.blocks) if a in b and q in b) == target
            )
    # Every other block meets the heavy triple in at most one point.
    for i, b in enumerate(universe.blocks):
        if len(set(b) & {1, 2, 3}) >= 2 and i not in fixed_ids:
            model.add(xs[i] == 0)
    if count_cuts:
        add_heavy_count_cuts(universe, model, xs)
    return universe, model, xs, holes, private


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=300)
    parser.add_argument("--max-missing", type=int, default=0)
    parser.add_argument("--seed", type=int, default=2026101801)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--count-cuts", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0 or args.workers < 1:
        parser.error("positive finite budget and positive worker count required")
    args.output.mkdir(parents=True, exist_ok=True)
    universe, model, xs, holes, private = build_heavy_model(args.max_missing, args.count_cuts)
    sources = {}
    for name in ["heavy_triple_search.py", "essential_regular_search.py"]:
        raw = Path(__file__).with_name(name).read_bytes()
        (args.output / name).write_bytes(raw)
        sources[name] = hashlib.sha256(raw).hexdigest()
    model_file = args.output / "model.pbtxt"
    model.export_to_file(str(model_file))
    metadata = {
        "sources": sources,
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "solver_version": ortools.__version__,
        "seed": args.seed,
        "seconds": args.seconds,
        "workers": args.workers,
        "max_missing": args.max_missing,
        "count_cuts": args.count_cuts,
        "fixed_blocks": FIXED,
        "model_sha256": hashlib.sha256(model_file.read_bytes()).hexdigest(),
        "scope": "Regular point-essential64 covers containing a multiplicity7 triple; "
        "positive-hole mode searches a restricted family of partial covers.",
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = args.seed
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    with (args.output / "solver.log").open("w") as log:
        solver.log_callback = lambda line: log.write(line + "\n")
        status = solver.solve(model)
    result = {
        "status": solver.status_name(status),
        "seconds": solver.wall_time,
        "response_stats": solver.response_stats(),
        "cover_found": False,
    }
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        blocks = [b for i, b in enumerate(universe.blocks) if solver.value(xs[i])]
        candidate = args.output / "candidate.txt"
        write_blocks(candidate, blocks)
        package = verify_cover(blocks)
        proc = subprocess.run(
            [sys.executable, "scripts/check_cover.py", str(candidate), "--expected-blocks", "64"],
            capture_output=True,
            text=True,
        )
        if proc.returncode not in (0, 1):
            raise RuntimeError(proc.stderr)
        standalone = json.loads(proc.stdout)
        if len(package["uncovered"]) != standalone["uncovered_count"]:
            raise RuntimeError("cover checkers disagree")
        counts = Counter(t for b in blocks for t in combinations(b, 3))
        if counts[(1, 2, 3)] != 7 or unsupported_incidences(blocks):
            raise RuntimeError("heavy or essential property failed")
        if Counter(p for b in blocks for p in b) != Counter({p: 20 for p in range(1, 17)}):
            raise RuntimeError("regularity check failed")
        if args.count_cuts:
            heavy = [t for t, n in counts.items() if n >= 6]
            weight = sum(4 if counts[t] == 7 else 3 for t in heavy)
            if max(counts.values()) > 7 or weight > 16:
                raise RuntimeError("heavy count check failed")
            if len({p for t in heavy for p in t}) != 3 * len(heavy):
                raise RuntimeError("heavy disjointness check failed")
        result.update(
            package=package,
            standalone=standalone,
            uncovered=standalone["uncovered_count"],
            cover_found=standalone["valid"],
        )
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in ("package", "standalone", "response_stats")
            }
        )
    )


if __name__ == "__main__":
    main()
