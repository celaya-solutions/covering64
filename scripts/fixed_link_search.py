#!/usr/bin/env python3
# Document:    Fixed Point Link Cover Search
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Complete a prescribed point link; conclusions concern only that fixed link."""

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import (
    Universe,
    normalize_blocks,
    read_blocks,
    schonheim_bound,
    verify_cover,
    write_blocks,
)


def build_fixed_link_model(universe, link, target):
    """Fix all blocks containing v to link blocks extended by v.

    This is a restricted model, not a complete reduction of unrestricted search.
    Within that restriction, all remaining blocks are present in full-universe
    lexicographic order. Bounds on subset links follow the recursive Schonheim
    bound for C(v-s,k-s,t-s), so add no further restrictions on genuine covers.
    """
    if universe.t < 2:
        raise ValueError("fixed links require t >= 2")
    link = normalize_blocks(link, universe.v - 1, universe.k - 1)
    checked = verify_cover(link, universe.v - 1, universe.k - 1, universe.t - 1)
    if not checked["valid"]:
        raise ValueError("the supplied link does not cover every required subset")
    if type(target) is not int or target < checked["blocks"]:
        raise ValueError("target must be an integer at least the link size")
    fixed = {tuple(block) + (universe.v,) for block in link}
    fixed_ids = [i for i, block in enumerate(universe.blocks) if block in fixed]
    candidates = [i for i, block in enumerate(universe.blocks) if universe.v not in block]
    model = cp_model.CpModel()
    variables = {i: model.NewBoolVar(f"block_{i}") for i in candidates}
    covered = {triple for i in fixed_ids for triple in universe.coverage[i]}
    deficient = [i for i in range(len(universe.triples)) if i not in covered]
    for triple in deficient:
        model.AddBoolOr([variables[i] for i in universe.containing[triple] if i in variables])
    model.Add(sum(variables.values()) <= target - len(fixed))
    block_sets = [set(block) for block in universe.blocks]
    for size in range(1, universe.t):
        lower = schonheim_bound(universe.v - size, universe.k - size, universe.t - size)
        for subset in combinations(range(1, universe.v + 1), size):
            required = set(subset)
            fixed_count = sum(required <= block_sets[i] for i in fixed_ids)
            model.Add(sum(variables[i] for i in candidates if required <= block_sets[i])
                      >= lower - fixed_count)
    return model, variables, fixed_ids, deficient


def standalone_check(path, v, k, t, expected=None):
    command = [sys.executable, str(Path(__file__).with_name("check_cover.py")), str(path),
               "--v", str(v), "--k", str(k), "--t", str(t)]
    if expected is not None:
        command += ["--expected-blocks", str(expected)]
    run = subprocess.run(command, capture_output=True, text=True, check=False)
    report = json.loads(run.stdout)
    if run.returncode or not report["valid"]:
        raise ValueError("standalone checker rejected witness")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("link", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=600)
    parser.add_argument("--seed", type=int, default=2026100364)
    parser.add_argument("--target", type=int, default=64)
    parser.add_argument("--hint", type=Path)
    parser.add_argument("--expected-link-blocks", type=int, default=19)
    args = parser.parse_args(argv)
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("seconds must be finite and positive")
    universe = Universe.build()
    link = read_blocks(args.link, 15, 4)
    independent_link = standalone_check(args.link, 15, 4, 2, expected=args.expected_link_blocks)
    link_check = verify_cover(link, 15, 4, 2)
    if not link_check["valid"] or len(link) != args.expected_link_blocks:
        parser.error(f"expected a verified {args.expected_link_blocks}-block C(15,4,2) link")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "source_snapshot.py").write_bytes(Path(__file__).read_bytes())
    write_blocks(args.output / "link.txt", link)
    model, variables, fixed_ids, deficient = build_fixed_link_model(universe, link, args.target)
    if args.hint:
        hint = set(read_blocks(args.hint))
        for block_id, variable in variables.items():
            model.AddHint(variable, int(universe.blocks[block_id] in hint))
    model_path = args.output / "model.pbtxt"
    model.ExportToFile(str(model_path))
    metadata = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "solver": "OR-Tools CP-SAT", "solver_version": ortools.__version__,
        "seed": args.seed, "workers": 2, "seconds": args.seconds, "target": args.target,
        "fixed_ids": fixed_ids, "candidates": len(variables), "deficient": len(deficient),
        "link_verification": link_check, "standalone_link_verification": independent_link,
        "hint_sha256": hashlib.sha256(args.hint.read_bytes()).hexdigest() if args.hint else None,
        "repair_hint": bool(args.hint), "hint_conflict_limit": 10000 if args.hint else None,
        "scope": "only completions of this prescribed point-16 link; no global inference",
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = 2
    solver.parameters.random_seed = args.seed % 2_147_483_647
    if args.hint:
        solver.parameters.repair_hint = True
        solver.parameters.hint_conflict_limit = 10000
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    started = time.monotonic()
    with (args.output / "solver.log").open("w") as log:
        solver.log_callback = lambda message: (log.write(message + "\n"), log.flush())
        status = solver.Solve(model)
    result = {"status": solver.StatusName(status), "solver_seconds": solver.WallTime(),
              "elapsed_seconds": time.monotonic() - started,
              "scope": metadata["scope"], "witness": None,
              "response_stats": solver.ResponseStats()}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        selected = sorted(fixed_ids + [i for i in variables if solver.Value(variables[i])])
        witness = [universe.blocks[i] for i in selected]
        checked = verify_cover(witness)
        if not checked["valid"] or len(witness) > args.target:
            raise RuntimeError("fixed-link solver candidate failed full package verification")
        path = args.output / f"cover-{len(witness)}.txt"
        write_blocks(path, witness)
        result.update(witness=witness, verification=checked,
                      standalone_verification=standalone_check(path, 16, 5, 3))
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
