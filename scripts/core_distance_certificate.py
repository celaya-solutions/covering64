# Document:    Rigid core distance certificate generation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Certify restricted core neighborhoods; this is not a global lower bound."""

import argparse
import hashlib
import json
import subprocess
import time
from collections import Counter
from fractions import Fraction
from itertools import combinations
from pathlib import Path

import ortools

from covering64.core import Universe, read_blocks, verify_cover
from scripts.residual_lp import residual_dual


def generate(start, maximum_removed, output):
    universe = Universe.build()
    blocks = read_blocks(start)
    if not verify_cover(blocks)["valid"]:
        raise ValueError("Input must be a verified complete cover")
    counts = Counter(t for b in blocks for t in combinations(b, 3))
    core = [b for b in blocks
            if len({p for t in combinations(b, 3) if counts[t] == 1 for p in t}) == 5]
    lookup = {b: i for i, b in enumerate(universe.blocks)}
    ids = [lookup[b] for b in core]
    records = []
    started = time.monotonic()
    minimum_margin = None
    for size in range(maximum_removed + 1):
        for removed in combinations(range(len(core)), size):
            keep = [b for i, b in enumerate(ids) if i not in removed]
            dual = residual_dual(universe, keep)
            budget = 64 - len(keep)
            margin = Fraction(*dual["lower_bound"]) - budget
            if margin <= 0:
                print(json.dumps({"uncertified": removed, "bound": dual["lower_bound"]}),
                      flush=True)
                raise RuntimeError("Requested universal obstruction was not certified")
            minimum_margin = margin if minimum_margin is None else min(minimum_margin, margin)
            records.append({"removed_core_indices": removed, **dual})
            if len(records) % 100 == 0:
                print(json.dumps({"checked": len(records), "minimum_margin": str(minimum_margin),
                                  "seconds": time.monotonic() - started}), flush=True)
    result = {"scope": "64-block covers retaining these core blocks except listed removals",
              "v": 16, "k": 5, "t": 3, "target": 64, "core": core,
              "maximum_removed": maximum_removed, "records": records,
              "minimum_margin": str(minimum_margin), "elapsed_seconds": time.monotonic()-started,
              "ortools_version": ortools.__version__,
              "source_revision": subprocess.check_output(
                  ["git", "rev-parse", "HEAD"], text=True).strip(),
              "source_hashes": {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [Path(__file__), Path("scripts/residual_lp.py")]},
              "input_sha256": hashlib.sha256(start.read_bytes()).hexdigest()}
    output.write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print(json.dumps({"complete": len(records), "minimum_margin": str(minimum_margin),
                      "output": str(output)}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=Path, default=Path("data/baselines/belic-1997.txt"))
    parser.add_argument("--maximum-removed", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    generate(args.start, args.maximum_removed, args.output)
