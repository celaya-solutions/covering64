# Document:    Point essential regular neighborhood optimization
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      da1c5ffc0a844f062739c6875fe88b5e74df3c67af679d406a7e1872d0ba12bb
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Bounded neighborhood optimization from a verified essential regular partial cover."""

import argparse
import hashlib
import json
import math
import random
import subprocess
import sys
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

import ortools
from essential_regular_search import build_model, unsupported_incidences
from ortools.sat.python import cp_model

from covering64.core import read_blocks, verify_cover, write_blocks


def check(blocks, path):
    if len(blocks) != 64 or unsupported_incidences(blocks):
        raise ValueError("expected64 point-essential blocks")
    if Counter(p for b in blocks for p in b) != Counter({p: 20 for p in range(1, 17)}):
        raise ValueError("expected degree20")
    pairs = Counter(p for b in blocks for p in combinations(b, 2))
    if len(pairs) != 120 or min(pairs.values()) < 5:
        raise ValueError("pair incidence bound violated")
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
    if standalone["uncovered_count"] != len(package["uncovered"]):
        raise RuntimeError("cover checkers disagree")
    return {"package": package, "standalone": standalone}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seed_file", type=Path)
    parser.add_argument("--seconds", type=float, default=600)
    parser.add_argument("--slice", type=float, default=15)
    parser.add_argument("--seed", type=int, default=2026101600)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if any(not math.isfinite(v) or v <= 0 for v in [args.seconds, args.slice]):
        parser.error("positive finite budgets required")
    args.output.mkdir(parents=True, exist_ok=True)
    original = read_blocks(args.seed_file)
    first = min(original)
    labels = list(first) + [p for p in range(1, 17) if p not in first]
    mapping = dict(zip(labels, range(1, 17)))
    start = sorted(tuple(sorted(mapping[p] for p in b)) for b in original)
    verification = check(start, args.output / "initial.txt")
    best = verification["standalone"]["uncovered_count"]
    universe, base, xs, holes, private = build_model(best)
    rank = {b: i for i, b in enumerate(universe.blocks)}
    current = {rank[b] for b in start}
    sources = {}
    for name in ["essential_lns.py", "essential_regular_search.py"]:
        raw = Path(__file__).with_name(name).read_bytes()
        sources[name] = hashlib.sha256(raw).hexdigest()
        (args.output / name).write_bytes(raw)
    metadata = {
        "seed": args.seed,
        "seconds": args.seconds,
        "slice_seconds": args.slice,
        "workers": 1,
        "sizes": [8, 12, 16, 20, 24, 28],
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "sources": sources,
        "solver_version": ortools.__version__,
        "input_sha256": hashlib.sha256(args.seed_file.read_bytes()).hexdigest(),
        "permutation": mapping,
        "initial_check": verification,
        "scope": "bounded restricted neighborhoods, not a global nonexistence test",
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    rng = random.Random(args.seed)
    began = time.monotonic()
    records = []
    attempt = 0
    while time.monotonic() - began < args.seconds:
        size = metadata["sizes"][attempt % len(metadata["sizes"])]
        counts = Counter(t for b in current for t in universe.coverage[b])
        missing = [t for t in range(560) if counts[t] == 0]
        if attempt % 2 == 0 and missing:
            focus = set(universe.triples[rng.choice(missing)])
            ordered = sorted(
                current, key=lambda b: (-len(focus.intersection(universe.blocks[b])), rng.random())
            )
            removed = set(ordered[:size])
        else:
            removed = set(rng.sample(sorted(current), size))
        model = base.clone()
        for b in current - removed:
            model.add(xs[b] == 1)
        for b, x in enumerate(xs):
            model.add_hint(x, int(b in current))
        for t in range(560):
            model.add_hint(holes[t], int(counts[t] == 0))
            model.add_hint(private[t], int(counts[t] == 1))
        model.add(sum(holes) <= best)
        # A one-hole improvement beats every possible tie-break change. On an
        # equal-deficit plateau, prefer replacing more of the removed blocks.
        model.minimize((size + 1) * sum(holes) + sum(xs[b] for b in removed))
        folder = args.output / f"attempt-{attempt:04}"
        folder.mkdir()
        model_path = folder / "model.pbtxt"
        model.export_to_file(str(model_path))
        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = args.seed + attempt
        remaining = args.seconds - (time.monotonic() - began)
        if remaining <= 0:
            break
        solver.parameters.max_time_in_seconds = min(args.slice, remaining)
        status = solver.solve(model)
        result = {
            "attempt": attempt,
            "seed": args.seed + attempt,
            "size": size,
            "status": solver.status_name(status),
            "seconds": solver.wall_time,
            "retained_ids": sorted(current - removed),
            "removed_ids": sorted(removed),
            "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
            "response_stats": solver.response_stats(),
        }
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            ids = {b for b, x in enumerate(xs) if solver.value(x)}
            candidate = [universe.blocks[b] for b in sorted(ids)]
            verified = check(candidate, folder / "candidate.txt")
            uncovered = verified["standalone"]["uncovered_count"]
            if uncovered > best:
                raise RuntimeError("neighborhood worsened its enforced deficit bound")
            result.update(uncovered=uncovered, changed_blocks=len(current - ids), checks=verified)
            current = ids
            if uncovered < best:
                best = uncovered
                write_blocks(args.output / f"best-{best}.txt", candidate)
        records.append(result)
        (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(
            json.dumps(
                {k: result.get(k) for k in ["attempt", "status", "uncovered", "changed_blocks"]}
            ),
            flush=True,
        )
        attempt += 1
        if best == 0:
            break
    (args.output / "summary.json").write_text(
        json.dumps(
            {
                "best_uncovered": best,
                "elapsed_seconds": time.monotonic() - began,
                "attempts": records,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
