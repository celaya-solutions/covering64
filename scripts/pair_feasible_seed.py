# Document:    Degree and pair constrained seed repair
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Enumerate all single point exchanges between two blocks of a regular seed."""

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from itertools import combinations
from pathlib import Path

from covering64.core import Universe, read_blocks, verify_cover, write_blocks


def search(start, output):
    universe = Universe.build()
    initial = read_blocks(start)
    if len(initial) != 64 or Counter(p for b in initial for p in b) != Counter(
        {p: 20 for p in range(1, 17)}
    ):
        raise ValueError("Input must have 64 blocks and exactly 20 occurrences per point")
    lookup = {b: i for i, b in enumerate(universe.blocks)}
    ids = [lookup[b] for b in initial]
    selected = set(ids)
    pair_ids = {p: i for i, p in enumerate(combinations(range(1, 17), 2))}
    pairs = [[pair_ids[p] for p in combinations(b, 2)] for b in universe.blocks]
    pair_counts = Counter(t for i in ids for t in pairs[i])
    triple_counts = Counter(t for i in ids for t in universe.coverage[i])
    initial_missing = 560 - len(triple_counts)
    low_pairs = {p for p in range(120) if pair_counts[p] < 5}
    tried = 0
    found = Counter()
    best = 561
    output.mkdir(parents=True, exist_ok=True)
    for a, b in combinations(range(64), 2):
        old_a, old_b = initial[a], initial[b]
        for x in set(old_a) - set(old_b):
            for y in set(old_b) - set(old_a):
                new_a = lookup[tuple(sorted(set(old_a) - {x} | {y}))]
                new_b = lookup[tuple(sorted(set(old_b) - {y} | {x}))]
                if new_a == new_b or (selected - {ids[a], ids[b]}) & {new_a, new_b}:
                    continue
                tried += 1
                delta = Counter(pairs[new_a] + pairs[new_b])
                delta.subtract(pairs[ids[a]] + pairs[ids[b]])
                if any(pair_counts[p] + delta[p] < 5 for p in low_pairs | set(delta)):
                    continue
                change = Counter(universe.coverage[new_a] + universe.coverage[new_b])
                change.subtract(universe.coverage[ids[a]] + universe.coverage[ids[b]])
                missing = initial_missing + sum((triple_counts[t] + d == 0) -
                                                (triple_counts[t] == 0)
                                                for t, d in change.items())
                found[missing] += 1
                if missing < best:
                    best = missing
                    candidate = list(initial)
                    candidate[a], candidate[b] = universe.blocks[new_a], universe.blocks[new_b]
                    if len(verify_cover(candidate)["uncovered"]) != missing:
                        raise RuntimeError("Coverage accounting failed")
                    write_blocks(output / "best64.txt", candidate)
                    print(json.dumps({"best_deficit": best, "swap_slots": [a, b],
                                      "swap_points": [x, y]}), flush=True)
    result = {"tried": tried, "feasible_histogram": dict(found),
              "best_deficit": best if found else None,
              "scope": "all single-point pair exchanges from this specific seed",
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "start_sha256": hashlib.sha256(start.read_bytes()).hexdigest(),
              "source_revision": subprocess.check_output(
                  ["git", "rev-parse", "HEAD"], text=True).strip()}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("start", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    search(args.start, args.output)
