#!/usr/bin/env python3
# Document:    Bounded Double Hub Extension Search
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Search fixed unions with complete nonanchor variables and checked dual pruning.

If a residual dual has total B and at most m blocks may be added, every selected
block has dual load at least B-m+1. For a positive-weight triple of weight w,
its coverage is at most1+floor((m-B)/w). The imported dual routine independently
checks the rational weights, all4368 capacities, and support on missing triples.
All further constraints are full-cover point/pair link lower bounds. The fixed
two point links and retained32 blocks remain explicit neighborhood restrictions.
"""

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from fractions import Fraction
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import Universe, schonheim_bound, verify_cover, write_blocks

spec = importlib.util.spec_from_file_location(
    "double_hub_dual", Path(__file__).with_name("lns_search.py"))
duals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(duals)


def solve_extension(universe, retained, certificate, seconds, seed, target=64,
                    anchors=(1, 2), output=None):
    retained = list(retained)
    if (len(retained) != len(set(retained))
            or any(type(i) is not int or not 0 <= i < len(universe.blocks) for i in retained)):
        raise ValueError("invalid or duplicate retained block IDs")
    if type(target) is not int or target < len(retained):
        raise ValueError("invalid target")
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("time budget must be finite and positive")
    covered = {t for i in retained for t in universe.coverage[i]}
    missing = sorted(set(range(len(universe.triples))) - covered)
    if any(set(universe.triples[t]) & set(anchors) for t in missing):
        raise ValueError("retained blocks do not close both anchor links")
    candidates = [i for i, b in enumerate(universe.blocks)
                  if not set(b) & set(anchors) and i not in retained]
    budget = target - len(retained)
    bound = Fraction(*certificate["lower_bound"])
    allowed, upper, reduction = duals.dual_restrictions(
        universe, certificate, max(budget, math.ceil(bound)), candidates, missing)
    result = {"retained_ids": sorted(retained), "target": target, "replacement_limit": budget,
              "complete_candidate_count": len(candidates), "candidate_count": len(allowed),
              "certificate": certificate, "reduction": reduction, "seed": seed,
              "seconds": seconds, "workers": 2, "witness": None,
              "scope": "only this retained union with closed anchor links; no global inference"}
    if bound > budget:
        result.update(status="LP_CERTIFIED_INFEASIBLE", solver_seconds=0.0)
        return result
    model = cp_model.CpModel()
    variables = {i: model.NewBoolVar(f"block_{i}") for i in allowed}
    for t in missing:
        terms = [variables[i] for i in universe.containing[t] if i in variables]
        model.Add(sum(terms) >= 1)
        if t in upper:
            model.Add(sum(terms) <= upper[t])
    model.Add(sum(variables.values()) <= budget)
    block_sets = [set(b) for b in universe.blocks]
    for size in range(1, universe.t):
        lower = schonheim_bound(universe.v - size, universe.k - size, universe.t - size)
        for subset in combinations(range(1, universe.v + 1), size):
            point_set = set(subset)
            fixed = sum(point_set <= block_sets[i] for i in retained)
            model.Add(sum(variables[i] for i in allowed if point_set <= block_sets[i])
                      + fixed >= lower)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 2
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.random_seed = seed % 2_147_483_647
    solver.parameters.log_search_progress = output is not None
    solver.parameters.log_to_stdout = False
    if output:
        output.mkdir(parents=True, exist_ok=True)
        model.ExportToFile(str(output / "model.pbtxt"))
        result["model_sha256"] = hashlib.sha256((output / "model.pbtxt").read_bytes()).hexdigest()
        with (output / "solver.log").open("w") as stream:
            solver.log_callback = lambda line: (stream.write(line + "\n"), stream.flush())
            status = solver.Solve(model)
    else:
        status = solver.Solve(model)
    result.update(status=solver.StatusName(status), solver_seconds=solver.WallTime(),
                  response_stats=solver.ResponseStats())
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        ids = sorted(set(retained) | {i for i in allowed if solver.Value(variables[i])})
        witness = [universe.blocks[i] for i in ids]
        checked = verify_cover(witness, universe.v, universe.k, universe.t)
        if not checked["valid"] or len(witness) > target:
            raise RuntimeError("extension failed package verification")
        result.update(witness=witness, verification=checked)
    return result


def build_pool_summary(universe, cases, representatives, target):
    """Compute queue priorities afresh; solve_extension rechecks every reduction."""
    candidates = [i for i, block in enumerate(universe.blocks)
                  if not set(block) & {1, 2}]
    rows = []
    for index in representatives:
        case = cases[index]
        certificate = case["certificate"]
        budget = target - len(case["retained_block_ids"])
        bound = Fraction(*certificate["lower_bound"])
        if bound > budget:
            continue
        denominator = math.lcm(*(w[2] for w in certificate["weights"]))
        weights = {tid: numerator * (denominator // divisor)
                   for tid, numerator, divisor in certificate["weights"]}
        cutoff = (bound - budget + 1) * denominator
        count = sum(sum(weights.get(t, 0) for t in universe.coverage[i]) >= cutoff
                    for i in candidates)
        rows.append({"case": index, "identifier": case["identifier"],
                     "bound": [bound.numerator, bound.denominator],
                     "pool_size": count, "complete_pool_size": len(candidates),
                     "target": target})
    return rows


def choose_queue(pools, cases, reduced_seconds, broad_seconds, per_class, skip_reduced):
    queue = ([] if skip_reduced else
             sorted([dict(row, seconds=reduced_seconds) for row in pools
                     if row["pool_size"] < row["complete_pool_size"]],
                    key=lambda row: (row["pool_size"], row["case"])))
    queued = {row["case"] for row in queue}
    for label in ("1", "4", "44", "47"):
        candidates = sorted([row for row in pools
                             if cases[row["case"]]["first_class"] == label
                             and row["case"] not in queued],
                            key=lambda row: (Fraction(*row["bound"]), row["case"]))
        for row in candidates[:per_class]:
            queue.append(dict(row, seconds=broad_seconds))
            queued.add(row["case"])
    return queue


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("unions", type=Path)
    parser.add_argument("certificates", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reduced-seconds", type=float, default=5)
    parser.add_argument("--broad-seconds", type=float, default=20)
    parser.add_argument("--seed", type=int, default=2026101300)
    parser.add_argument("--target", type=int, choices=(64, 65), default=64)
    parser.add_argument("--per-class", type=int, default=2)
    parser.add_argument("--skip-reduced", action="store_true")
    args = parser.parse_args(argv)
    if args.per_class < 0 or any(not math.isfinite(s) or s <= 0
                               for s in (args.reduced_seconds, args.broad_seconds)):
        parser.error("nonnegative per-class count and positive finite budgets required")
    raw = args.certificates.read_bytes()
    certificates = json.loads(gzip.decompress(raw))
    quotient_raw = (args.unions / "anchor-reversal-quotient.json").read_bytes()
    quotient = json.loads(quotient_raw)
    universe = Universe.build()
    pools = build_pool_summary(universe, certificates["cases"],
                               quotient["representative_case_ids"], args.target)
    queue = choose_queue(pools, certificates["cases"], args.reduced_seconds,
                         args.broad_seconds, args.per_class, args.skip_reduced)
    args.output.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).read_bytes()
    helper = Path(__file__).with_name("lns_search.py").read_bytes()
    (args.output / "source.py").write_bytes(source)
    (args.output / "dual-source.py").write_bytes(helper)
    metadata = {"source_sha256": hashlib.sha256(source).hexdigest(),
                "dual_source_sha256": hashlib.sha256(helper).hexdigest(),
                "certificates_sha256": hashlib.sha256(raw).hexdigest(),
                "quotient_sha256": hashlib.sha256(quotient_raw).hexdigest(),
                "target": args.target, "skip_reduced": args.skip_reduced,
                "per_class": args.per_class,
                "solver_version": ortools.__version__, "workers": 2, "seed": args.seed,
                "source_revision": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True).strip(),
                "queue": queue, "scope": "bounded search on listed fixed32-block neighborhoods"}
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (args.output / "pool-summary.json").write_text(json.dumps(pools, indent=2) + "\n")
    results = []
    for number, row in enumerate(queue):
        case = certificates["cases"][row["case"]]
        folder = args.output / case["identifier"]
        result = solve_extension(universe, case["retained_block_ids"], case["certificate"],
                                 row["seconds"], args.seed + number,
                                 target=args.target, output=folder)
        result.update(case=row["case"], identifier=case["identifier"])
        if result["witness"]:
            path = folder / "cover.txt"
            write_blocks(path, result["witness"])
            command = [sys.executable, "scripts/check_cover.py", str(path)]
            check = subprocess.run(command, capture_output=True, text=True, check=True)
            result["standalone_verification"] = json.loads(check.stdout)
            if not result["standalone_verification"]["valid"]:
                raise RuntimeError("extension failed standalone verification")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        results.append({k: result[k] for k in ("case", "identifier", "status", "solver_seconds",
                                              "candidate_count")})
        (args.output / "summary.json").write_text(json.dumps(results, indent=2) + "\n")
        print(json.dumps(results[-1]), flush=True)
        if result["witness"]:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
