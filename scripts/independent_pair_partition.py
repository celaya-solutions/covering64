#!/usr/bin/env python3
# Document:    Eight-Pair Excess-Support Construction Probe
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      d14801fe133af4a72af2447e396b8afbf4ac3efbb2c064bd0141b1a9bdc1da0c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Restricted construction search; negative solver status is not a theorem."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import Universe, verify_cover, write_blocks


def block_type(block):
    """Point labels are 1-based; pair groups are (1,2), (3,4), ..., (15,16)."""
    return tuple(sorted(Counter((point - 1) // 2 for point in block).values(), reverse=True))


def build_model(balanced_types=False):
    """Return all 4368 lexicographic block variables, with no degree assumptions.

    The restriction places all triple excess on triples containing a full pair.
    For block-type counts a=221, b=2111, c=11111, exact transversal coverage
    forces 2a+b=64 and c=a. balanced_types adds b=0, hence a=c=32.
    """
    if type(balanced_types) is not bool:
        raise ValueError("balanced_types must be a boolean")
    universe = Universe.build()
    model = cp_model.CpModel()
    selected = [model.new_bool_var(f"block_{i}") for i in range(len(universe.blocks))]
    model.add(sum(selected) == 64)
    for triple, containing in zip(universe.triples, universe.containing, strict=True):
        expression = sum(selected[i] for i in containing)
        if len({(point - 1) // 2 for point in triple}) == 3:
            model.add(expression == 1)
        else:
            model.add(expression >= 1)
    if balanced_types:
        model.add(sum(selected[i] for i, block in enumerate(universe.blocks)
                      if block_type(block) == (2, 1, 1, 1)) == 0)
    return universe, model, selected


def run(out, seconds, seed, balanced_types=False):
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("seconds must be finite and positive")
    out.mkdir(parents=True, exist_ok=False)
    source_bytes = Path(__file__).read_bytes()
    (out / "source.py").write_bytes(source_bytes)
    universe, model, selected = build_model(balanced_types)
    model.export_to_file(str(out / "model.pbtxt"))
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.random_seed = seed
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    started = time.time()
    with (out / "solver.log").open("w") as log:
        solver.log_callback = lambda text: (log.write(text + "\n"), log.flush())
        status = solver.solve(model)
    record = {
        "scope": "restricted eight-pair excess support; not an unrestricted reduction",
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "seed": seed,
        "budget_seconds": seconds,
        "workers": 1,
        "python": platform.python_version(),
        "ortools": ortools.__version__,
        "started_unix": started,
        "elapsed_seconds": time.time() - started,
        "status": solver.status_name(status),
        "stats": solver.response_stats(),
        "pair_partition": [[point, point + 1] for point in range(1, 17, 2)],
        "balanced_types": balanced_types,
        "block_variables": len(selected),
        "transversal_triples": 448,
        "nontransversal_triples": 112,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "model_sha256": hashlib.sha256((out / "model.pbtxt").read_bytes()).hexdigest(),
    }
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        blocks = [block for block, var in zip(universe.blocks, selected, strict=True)
                  if solver.value(var)]
        witness = out / "witness.txt"
        write_blocks(witness, blocks)
        record["witness_sha256"] = hashlib.sha256(witness.read_bytes()).hexdigest()
        record["package_verifier"] = verify_cover(blocks)
        check = subprocess.run(
            [sys.executable, "-I", "scripts/check_cover.py", str(witness),
             "--expected-blocks", "64"], capture_output=True, text=True, check=False,
        )
        record["standalone_verifier"] = {
            "exit_code": check.returncode, "report": json.loads(check.stdout),
        }
        counts = Counter(triple for block in blocks for triple in combinations(block, 3))
        record["partition_check"] = all(
            counts[triple] == 1 if len({(point - 1) // 2 for point in triple}) == 3
            else counts[triple] >= 1 for triple in universe.triples
        )
        record["block_type_counts"] = {
            "".join(map(str, kind)): count
            for kind, count in sorted(Counter(block_type(block) for block in blocks).items())
        }
        if (not record["package_verifier"]["valid"] or check.returncode != 0
                or not record["partition_check"]):
            raise RuntimeError("solver witness failed a covering or partition check")
    (out / "result.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: record[key] for key in
                      ("status", "elapsed_seconds", "seed", "balanced_types")}))
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--seed", type=int, default=640303)
    parser.add_argument("--balanced-types", action="store_true")
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("seconds must be finite and positive")
    run(args.out, args.seconds, args.seed, args.balanced_types)
