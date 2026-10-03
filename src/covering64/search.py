"""Exact bounded repairs of neighborhoods of an independently checked cover.

Neighborhood infeasibility describes the selected removal only and never
establishes a global lower bound.
"""

from __future__ import annotations

import math
import random
import time
from collections import Counter
from itertools import combinations
from typing import Iterable

from .core import Universe, normalize_blocks, verify_cover


def _checked_incumbent(
    universe: Universe, incumbent: Iterable[Iterable[int]]
) -> tuple[tuple[tuple[int, ...], ...], list[int], dict]:
    blocks = normalize_blocks(incumbent, universe.v, universe.k)
    verification = verify_cover(blocks, universe.v, universe.k, universe.t)
    if not verification["valid"]:
        raise ValueError("The incumbent must cover every required subset.")
    indices = {block: i for i, block in enumerate(universe.blocks)}
    return blocks, [indices[block] for block in blocks], verification


def _coverage_counts(universe: Universe, selected: Iterable[int]) -> list[int]:
    counts = [0] * len(universe.triples)
    for block_id in selected:
        for triple_id in universe.coverage[block_id]:
            counts[triple_id] += 1
    return counts


def _deficits(
    universe: Universe, removed: Iterable[int], counts: list[int]
) -> list[int]:
    removed_counts = Counter(
        triple_id
        for block_id in removed
        for triple_id in universe.coverage[block_id]
    )
    return sorted(
        triple_id
        for triple_id, count in removed_counts.items()
        if count == counts[triple_id]
    )


def run_exchange_search(
    universe: Universe,
    incumbent: Iterable[Iterable[int]],
    attempts: int = 20,
    remove: int = 4,
    seconds_per_attempt: float = 1.0,
    seed: int = 0,
) -> dict:
    """Try exact ``remove``-to-at-most-``remove - 1`` CP-SAT repairs.

    Cover every subset made deficient by removal, using distinct replacement
    blocks outside the retained incumbent. Independently verify each full
    resulting cover before accepting it as the next incumbent. The number
    removed is between three and six. Each attempt has a distinct solver seed
    and uses one worker; wall-clock limits can still affect reproducibility.

    ``no_improvement`` includes timeouts and is only a bounded search outcome.
    """
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 0:
        raise ValueError("attempts must be a nonnegative integer")
    if isinstance(remove, bool) or not isinstance(remove, int) or not 3 <= remove <= 6:
        raise ValueError("remove must be an integer between 3 and 6")
    if (
        isinstance(seconds_per_attempt, bool)
        or not isinstance(seconds_per_attempt, (int, float))
        or not math.isfinite(seconds_per_attempt)
        or seconds_per_attempt <= 0
    ):
        raise ValueError("seconds_per_attempt must be finite and positive")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")

    current, selected, verification = _checked_incumbent(universe, incumbent)
    initial_count = len(current)
    incumbent_sha256 = verification["canonical_sha256"]
    if attempts and remove > initial_count:
        raise ValueError("remove cannot exceed the incumbent block count")

    solver_version = None
    if attempts:
        import ortools
        from ortools.sat.python import cp_model

        solver_version = ortools.__version__

    rng = random.Random(seed)
    logs: list[dict] = []
    for attempt in range(attempts):
        if len(selected) < remove:
            break
        started = time.perf_counter()
        attempt_seed = (seed + attempt) % 2_147_483_647
        removed = sorted(rng.sample(selected, remove))
        retained = set(selected).difference(removed)
        deficient = _deficits(universe, removed, _coverage_counts(universe, selected))
        candidate_ids = sorted(
            {
                block_id
                for triple_id in deficient
                for block_id in universe.containing[triple_id]
                if block_id not in retained
            }
        )
        log = {
            "attempt": attempt + 1,
            "seed": attempt_seed,
            "incumbent_blocks": len(selected),
            "removed_ids": removed,
            "uncovered_triple_ids": deficient,
            "uncovered_triples": [universe.triples[i] for i in deficient],
            "candidate_count": len(candidate_ids),
            "replacement_limit": remove - 1,
            "solver_status": None,
            "solver_seconds": 0.0,
            "replacement_ids": [],
            "accepted": False,
            "scope": "selected removal neighborhood only",
        }
        replacement: list[int] | None = None
        if not deficient:
            log["solver_status"] = "TRIVIAL"
            replacement = []
        elif not candidate_ids:
            log["solver_status"] = "INFEASIBLE"
        else:
            model = cp_model.CpModel()
            variables = {
                block_id: model.NewBoolVar(f"block_{block_id}")
                for block_id in candidate_ids
            }
            for triple_id in deficient:
                model.AddBoolOr(
                    [variables[i] for i in universe.containing[triple_id] if i in variables]
                )
            model.Add(sum(variables.values()) <= remove - 1)
            model.Minimize(sum(variables.values()))
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = float(seconds_per_attempt)
            solver.parameters.random_seed = attempt_seed
            solver.parameters.num_search_workers = 1
            status = solver.Solve(model)
            log["solver_status"] = solver.StatusName(status)
            log["solver_seconds"] = solver.WallTime()
            if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                replacement = [i for i in candidate_ids if solver.Value(variables[i])]

        if replacement is not None:
            if len(replacement) > remove - 1 or retained.intersection(replacement):
                raise RuntimeError("The solver returned an invalid replacement.")
            next_ids = sorted(retained.union(replacement))
            candidate = tuple(universe.blocks[i] for i in next_ids)
            checked = verify_cover(candidate, universe.v, universe.k, universe.t)
            if not checked["valid"] or len(candidate) >= len(current):
                raise RuntimeError("A repair failed full independent verification.")
            current, selected, verification = candidate, next_ids, checked
            log["replacement_ids"] = replacement
            log["accepted"] = True
            log["result_blocks"] = len(current)
        log["elapsed_seconds"] = time.perf_counter() - started
        logs.append(log)

    improved = len(current) < initial_count
    return {
        "status": "improved" if improved else "no_improvement",
        "improved": improved,
        "initial_block_count": initial_count,
        "final_block_count": len(current),
        "incumbent_sha256": incumbent_sha256,
        "parameters": {"v": universe.v, "k": universe.k, "t": universe.t},
        "solver": {"name": "OR-Tools CP-SAT", "version": solver_version, "workers": 1},
        "witness": current if improved else None,
        "verification": verification,
        "attempts": logs,
        "requested_attempts": attempts,
        "completed_attempts": len(logs),
        "remove": remove,
        "seconds_per_attempt": float(seconds_per_attempt),
        "seed": seed,
        "scope": "bounded incumbent block-exchange search; no global inference",
    }


def audit_small_exchanges(
    universe: Universe, incumbent: Iterable[Iterable[int]]
) -> dict:
    """Exhaust every deletion and two-block-to-one-block replacement.

    A replacement must contain the union of points in every deficit. Enumerate
    all extensions of this union to one block, excluding retained blocks, and
    independently verify successful candidates. Record the total number of
    replacements for each pair and one representative. The scope is this
    incumbent only and cannot decide unrestricted covering feasibility.
    """
    blocks, selected, verification = _checked_incumbent(universe, incumbent)
    counts = _coverage_counts(universe, selected)
    selected_set = set(selected)
    block_ids = {block: i for i, block in enumerate(universe.blocks)}
    deletable: list[int] = []
    compressible: list[dict] = []
    witness = None
    witness_verification = None
    minimum_deficit = None
    minimum_pairs: list[list[int]] = []
    pair_checks = 0

    def check_witness(ids: Iterable[int]) -> tuple[tuple[tuple[int, ...], ...], dict]:
        candidate = tuple(universe.blocks[i] for i in sorted(ids))
        checked = verify_cover(candidate, universe.v, universe.k, universe.t)
        if not checked["valid"]:
            raise RuntimeError("An audited repair failed independent verification.")
        return candidate, checked

    for removed in selected:
        if not _deficits(universe, [removed], counts):
            deletable.append(removed)
            candidate, checked = check_witness(selected_set.difference([removed]))
            if witness is None:
                witness, witness_verification = candidate, checked

    for pair in combinations(selected, 2):
        pair_checks += 1
        deficient = _deficits(universe, pair, counts)
        deficit_count = len(deficient)
        if minimum_deficit is None or deficit_count < minimum_deficit:
            minimum_deficit = deficit_count
            minimum_pairs = [list(pair)]
        elif deficit_count == minimum_deficit:
            minimum_pairs.append(list(pair))
        union = {
            point for triple_id in deficient for point in universe.triples[triple_id]
        }
        if len(union) > universe.k:
            continue
        retained = selected_set.difference(pair)
        complement = [point for point in range(1, universe.v + 1) if point not in union]
        valid_replacements = []
        for extension in combinations(complement, universe.k - len(union)):
            replacement = tuple(sorted(union.union(extension)))
            replacement_id = block_ids[replacement]
            if replacement_id not in retained:
                valid_replacements.append(replacement_id)
        if valid_replacements:
            valid_replacements.sort()
            representative = valid_replacements[0]
            for candidate_id in valid_replacements:
                candidate, checked = check_witness(retained.union([candidate_id]))
                if witness is None:
                    witness, witness_verification = candidate, checked
            compressible.append(
                {
                    "removed_ids": list(pair),
                    "uncovered_triples": [universe.triples[i] for i in deficient],
                    "deficit_point_union": sorted(union),
                    "replacement_count": len(valid_replacements),
                    "replacement_id": representative,
                    "replacement": universe.blocks[representative],
                }
            )

    improved = witness is not None
    return {
        "status": "improved" if improved else "no_small_exchange",
        "improved": improved,
        "incumbent_blocks": len(blocks),
        "incumbent_sha256": verification["canonical_sha256"],
        "parameters": {"v": universe.v, "k": universe.k, "t": universe.t},
        "deletion_checks": len(blocks),
        "deletable_block_ids": deletable,
        "pair_checks": pair_checks,
        "compressible_pairs": compressible,
        "min_pair_deficit": minimum_deficit,
        "min_pair_deficit_pairs": minimum_pairs,
        "witness": witness,
        "verification": witness_verification if improved else verification,
        "scope": "all deletions and two-to-one exchanges of this incumbent only",
    }
