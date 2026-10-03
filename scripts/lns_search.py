#!/usr/bin/env python3
# Document:    Large Neighborhood Cover Search
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Bounded CP-SAT repairs of full or partial covers; no global lower-bound claims."""

import argparse
import hashlib
import importlib.util
import json
import math
import random
import subprocess
import sys
import time
from fractions import Fraction
from functools import lru_cache
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


@lru_cache(maxsize=1)
def _dual_function():
    path = Path(__file__).with_name("residual_lp.py")
    spec = importlib.util.spec_from_file_location("lns_residual_lp", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.residual_dual


def dual_restrictions(universe, certificate, budget, candidates, deficient=None):
    """Exactly certify load pruning and weighted-overlap bounds for full repairs.

    For at most m additions, sum of selected block loads is at least B and
    at most m. Each block deficit1-load and each weighted duplicate term
    w_t*(coverage_t-1) is nonnegative and individually at most slack=m-B.
    """
    weights = {t: Fraction(n, d) for t, n, d in certificate["weights"]}
    if (len(weights) != len(certificate["weights"])
            or any(type(t) is not int or not 0 <= t < len(universe.triples) for t in weights)
            or any(w < 0 for w in weights.values())):
        raise ValueError("invalid dual weights")
    if deficient is not None and not {t for t, w in weights.items() if w > 0} <= set(deficient):
        raise ValueError("positive dual weight on an already covered triple")
    bound = sum(weights.values(), Fraction(0))
    if bound != Fraction(*certificate["lower_bound"]):
        raise ValueError("dual bound does not equal its weight sum")
    loads = [sum((weights.get(t, Fraction(0)) for t in coverage), Fraction(0))
             for coverage in universe.coverage]
    if any(load > 1 for load in loads):
        raise ValueError("dual exceeds a block capacity")
    slack = budget - bound
    if slack < 0:
        raise ValueError("dual already excludes this repair budget")
    threshold = 1 - slack
    allowed = [i for i in candidates if loads[i] >= threshold]
    upper = {t: 1 + slack // weight for t, weight in weights.items() if weight > 0}
    return allowed, upper, {
        "slack": [slack.numerator, slack.denominator],
        "candidate_load_threshold": [threshold.numerator, threshold.denominator],
        "before_candidates": len(candidates), "after_candidates": len(allowed),
        "candidate_ids": allowed, "weighted_coverage_upper_bounds": sorted(upper.items()),
    }


def repair_neighborhood(
    universe, incumbent, removed, target, seconds, seed=0, change=False, exact=False,
    lp_screen=False, lp_prune=False,
):
    """Optimize missing subsets after fixing all unremoved incumbent blocks.

    Candidate IDs always follow the universe's lexicographic block order. Blocks
    covering no deficient subset can be omitted: the cardinality constraint is
    an upper bound, so deleting such a block cannot worsen coverage or feasibility.
    Missing-subset variables are exact indicators. The secondary objective prefers
    replacement blocks different from the incumbent, without sacrificing coverage.
    """
    blocks = normalize_blocks(incumbent, universe.v, universe.k)
    block_ids = {block: i for i, block in enumerate(universe.blocks)}
    selected = {block_ids[block] for block in blocks}
    removed = tuple(removed)
    if len(set(removed)) != len(removed) or any(type(i) is not int for i in removed):
        raise ValueError("removed IDs must be distinct integers")
    if not set(removed) <= selected:
        raise ValueError("removed IDs must belong to the incumbent")
    if type(target) is not int or target < 0:
        raise ValueError("target must be a nonnegative integer")
    if isinstance(seconds, bool) or not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("seconds must be finite and positive")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if (lp_screen or lp_prune) and not exact:
        raise ValueError("LP screening only applies to exact zero-deficit repairs")
    retained = selected - set(removed)
    budget = target - len(retained)
    if budget < 0:
        raise ValueError("target is smaller than the fixed retained set")
    counts = [0] * len(universe.triples)
    for block_id in retained:
        for triple in universe.coverage[block_id]:
            counts[triple] += 1
    deficient = [i for i, count in enumerate(counts) if not count]
    candidates = sorted({i for t in deficient for i in universe.containing[t]} - retained)
    certificate = None
    if lp_screen or lp_prune:
        started = time.monotonic()
        certificate = _dual_function()(universe, sorted(retained))
        if Fraction(*certificate["lower_bound"]) > budget:
            return {
                "status": "LP_CERTIFIED_INFEASIBLE", "solver_seconds": 0.0,
                "lp_seconds": time.monotonic() - started, "seed": seed, "target": target,
                "removed_ids": sorted(removed), "retained_ids": sorted(retained),
                "candidate_count": len(candidates), "deficient_count": len(deficient),
                "replacement_limit": budget, "lp_certificate": certificate,
                "scope": "only this retained-block neighborhood; no global inference",
                "exact": exact, "witness": None,
            }
    reduction = None
    upper = {}
    if lp_prune:
        candidates, upper, reduction = dual_restrictions(
            universe, certificate, budget, candidates, deficient)
    model = cp_model.CpModel()
    variables = {i: model.NewBoolVar(f"block_{i}") for i in candidates}
    for triple, limit in upper.items():
        model.Add(sum(variables[i] for i in universe.containing[triple] if i in variables) <= limit)
    missing = {}
    for triple in deficient:
        missing[triple] = model.NewBoolVar(f"missing_{triple}")
        coverers = [variables[i] for i in universe.containing[triple] if i in variables]
        model.AddBoolOr(coverers + [missing[triple]])
        for coverer in coverers:
            model.AddImplication(coverer, missing[triple].Not())
    model.Add(sum(variables.values()) <= budget)
    if exact:
        model.Add(sum(missing.values()) == 0)
        # Every s-subset link must cover all (t-s)-subsets on v-s points.
        # Recursive Schonheim bounds apply without incumbent symmetry assumptions.
        block_sets = [set(block) for block in universe.blocks]
        for size in range(1, universe.t):
            lower = schonheim_bound(universe.v - size, universe.k - size, universe.t - size)
            for subset in combinations(range(1, universe.v + 1), size):
                link = set(subset)
                fixed = sum(link <= block_sets[i] for i in retained)
                model.Add(sum(variables[i] for i in candidates if link <= block_sets[i])
                          >= lower - fixed)
    old_variables = [variables[i] for i in removed if i in variables]
    if change:
        model.Add(sum(old_variables) <= len(removed) - 1)
    model.Minimize((len(removed) + 1) * sum(missing.values()) + sum(old_variables))
    hint_selected = set(sorted(removed)[:budget])
    for i, variable in variables.items():
        model.AddHint(variable, int(i in hint_selected))
    for triple, variable in missing.items():
        uncovered = not any(i in hint_selected for i in universe.containing[triple])
        model.AddHint(variable, int(uncovered))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(seconds)
    solver.parameters.num_search_workers = 2
    solver.parameters.random_seed = seed % 2_147_483_647
    status = solver.Solve(model)
    result = {
        "status": solver.StatusName(status), "solver_seconds": solver.WallTime(),
        "seed": seed, "target": target, "removed_ids": sorted(removed),
        "retained_ids": sorted(retained), "candidate_count": len(candidates),
        "deficient_count": len(deficient), "replacement_limit": budget,
        "objective_bound": solver.BestObjectiveBound(),
        "scope": "only this retained-block neighborhood; no global inference",
        "exact": exact,
        "lp_certificate": certificate,
        "lp_reduction": reduction,
        "witness": None,
    }
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        replacement = [i for i in candidates if solver.Value(variables[i])]
        witness = [universe.blocks[i] for i in sorted(retained | set(replacement))]
        checked = verify_cover(witness, universe.v, universe.k, universe.t)
        uncovered = len(checked["uncovered"])
        if uncovered != sum(solver.Value(variable) for variable in missing.values()):
            raise RuntimeError("solver missing-subset score disagrees with full verification")
        if len(witness) > target:
            raise RuntimeError("solver violated cardinality limit")
        result.update(witness=witness, uncovered=uncovered, verification=checked,
                      replacement_ids=replacement, objective=solver.ObjectiveValue())
    return result


def choose_removed(universe, current, rng, size):
    """Mix uniform and deficit-focused removal without constraining replacements."""
    block_ids = {block: i for i, block in enumerate(universe.blocks)}
    selected = [block_ids[tuple(block)] for block in current]
    if size >= len(selected):
        return selected
    missing = verify_cover(current, universe.v, universe.k, universe.t)["uncovered"]
    if not missing or rng.random() < 0.35:
        return sorted(rng.sample(selected, size))
    focus = set(rng.choice(missing))
    weights = [(1 + len(focus.intersection(universe.blocks[i]))) ** 3 for i in selected]
    ranking = sorted(zip(selected, weights), key=lambda item: rng.random() ** (1 / item[1]),
                     reverse=True)
    return sorted(i for i, _ in ranking[:size])


def standalone_check(path, universe):
    command = [sys.executable, str(Path(__file__).with_name("check_cover.py")), str(path),
               "--v", str(universe.v), "--k", str(universe.k), "--t", str(universe.t)]
    checked = subprocess.run(command, capture_output=True, text=True, check=False)
    report = json.loads(checked.stdout)
    if checked.returncode or not report["valid"]:
        raise RuntimeError("independent standalone verifier rejected a full cover")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("witness", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=600)
    parser.add_argument("--slice-seconds", type=float, default=5)
    parser.add_argument("--sizes", default="6,8,10,12,16,20,26,32")
    parser.add_argument("--target", type=int, default=64)
    parser.add_argument("--seed", type=int, default=640003)
    parser.add_argument("--exact", action="store_true")
    parser.add_argument("--lp-screen", action="store_true")
    parser.add_argument("--lp-prune", action="store_true")
    args = parser.parse_args(argv)
    if any(not math.isfinite(x) or x <= 0 for x in (args.seconds, args.slice_seconds)):
        parser.error("time budgets must be finite and positive")
    if args.target <= 0:
        parser.error("target must be positive")
    if (args.lp_screen or args.lp_prune) and not args.exact:
        parser.error("--lp-screen and --lp-prune require --exact")
    sizes = [int(x) for x in args.sizes.split(",")]
    if not sizes or any(x <= 0 for x in sizes):
        parser.error("sizes must be positive")
    universe = Universe.build()
    baseline = list(read_blocks(args.witness))
    if not baseline:
        parser.error("witness must not be empty")
    rng = random.Random(args.seed)
    current = baseline[:]
    while len(current) > args.target:
        options = [(len(verify_cover(current[:i] + current[i + 1:])["uncovered"]), i)
                   for i in range(len(current))]
        minimum = min(score for score, _ in options)
        current.pop(rng.choice([i for score, i in options if score == minimum]))
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "source_snapshot.py").write_bytes(Path(__file__).read_bytes())
    if args.lp_screen or args.lp_prune:
        (args.output / "lp_source_snapshot.py").write_bytes(
            Path(__file__).with_name("residual_lp.py").read_bytes())
    best = current[:]
    best_score = len(verify_cover(best)["uncovered"])
    write_blocks(args.output / "best.txt", best)
    metadata = {"seed": args.seed, "seconds": args.seconds,
                "slice_seconds": args.slice_seconds, "sizes": sizes,
                "target": args.target, "solver": ortools.__version__, "workers": 2,
                "exact": args.exact,
                "lp_screen": args.lp_screen,
                "lp_prune": args.lp_prune,
                "lp_source_sha256": hashlib.sha256(
                    Path(__file__).with_name("residual_lp.py").read_bytes()
                ).hexdigest() if args.lp_screen or args.lp_prune else None,
                "source_revision": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True).strip(),
                "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "baseline_sha256": hashlib.sha256(args.witness.read_bytes()).hexdigest(),
                "initial_uncovered": best_score,
                "scope": "bounded neighborhood search; no global lower-bound inference"}
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    started = time.monotonic()
    attempt = 0
    stale = 0
    with (args.output / "attempts.jsonl").open("w") as logs:
        while time.monotonic() - started < args.seconds:
            remaining = args.seconds - (time.monotonic() - started)
            size = sizes[attempt % len(sizes)]
            removed = choose_removed(universe, current, rng, size)
            result = repair_neighborhood(universe, current, removed, args.target,
                                         min(args.slice_seconds, remaining),
                                         args.seed + attempt, change=True, exact=args.exact,
                                         lp_screen=args.lp_screen, lp_prune=args.lp_prune)
            result["attempt"] = attempt
            result["requested_seconds"] = min(args.slice_seconds, remaining)
            witness = result.pop("witness")
            if witness is not None:
                score = result["uncovered"]
                current_score = len(verify_cover(current)["uncovered"])
                accepted = score <= current_score or (
                    stale > 2 * len(sizes) and score <= best_score + 2 and rng.random() < 0.1)
                result["accepted"] = accepted
                if accepted:
                    current = witness
                if score < best_score:
                    best, best_score, stale = witness, score, 0
                    write_blocks(args.output / "best.txt", best)
                    (args.output / "best.json").write_text(json.dumps(result, indent=2) + "\n")
                    print(json.dumps({"attempt": attempt, "best_uncovered": best_score,
                                      "elapsed": time.monotonic() - started}), flush=True)
                if score == 0:
                    path = args.output / f"cover-{len(witness)}.txt"
                    write_blocks(path, witness)
                    result["standalone_verification"] = standalone_check(path, universe)
                    logs.write(json.dumps(result) + "\n")
                    logs.flush()
                    break
            logs.write(json.dumps(result) + "\n")
            logs.flush()
            attempt += 1
            stale += 1
            if stale > 4 * len(sizes):
                current, stale = best[:], 0
    summary = {"attempts": attempt, "best_uncovered": best_score,
               "elapsed_seconds": time.monotonic() - started,
               "best_verification": verify_cover(best)}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
