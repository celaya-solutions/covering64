#!/usr/bin/env python3
# Document:    Core Escape Large Neighborhood Search
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Heuristic partial-cover search with explicit, recorded core escape constraints."""

import argparse
import gzip
import hashlib
import json
import math
import random
import subprocess
import sys
import time
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import Universe, read_blocks, schonheim_bound, verify_cover, write_blocks


def digest_ids(ids):
    return hashlib.sha256(json.dumps(sorted(ids), separators=(",", ":")).encode()).hexdigest()


def solve_step(universe, selected, removed, core, seconds, seed, max_missing=6,
               core_cap=None, output=None, full_link_bounds=False):
    selected, removed, core = list(selected), list(removed), list(core)
    if any(len(ids) != len(set(ids)) for ids in (selected, removed, core)):
        raise ValueError("duplicate block IDs")
    selected, removed, core = set(selected), set(removed), set(core)
    if not removed <= selected or any(type(i) is not int or not 0 <= i < len(universe.blocks)
                                      for i in selected | core):
        raise ValueError("invalid selected, removed or core block IDs")
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("seconds must be finite and positive")
    if type(max_missing) is not int or max_missing < 0:
        raise ValueError("max_missing must be a nonnegative integer")
    if core_cap is not None and (type(core_cap) is not int or core_cap < 0):
        raise ValueError("core_cap must be a nonnegative integer")
    retained = selected - removed
    fixed_coverage = {t for i in retained for t in universe.coverage[i]}
    missing_ids = sorted(set(range(len(universe.triples))) - fixed_coverage)
    candidates = sorted(set(range(len(universe.blocks))) - retained)
    model = cp_model.CpModel()
    variables = {i: model.NewBoolVar(f"block_{i}") for i in candidates}
    missing = {t: model.NewBoolVar(f"missing_{t}") for t in missing_ids}
    for triple, flag in missing.items():
        terms = [variables[i] for i in universe.containing[triple] if i in variables]
        model.Add(sum(terms) == 0).OnlyEnforceIf(flag)
        model.Add(sum(terms) >= 1).OnlyEnforceIf(flag.Not())
    model.Add(sum(variables.values()) == len(removed))
    model.Add(sum(missing.values()) <= max_missing)
    if full_link_bounds:
        # Necessary for a full cover, though intentionally not for all partial
        # covers: every s-subset link covers (t-s)-subsets on v-s points.
        block_sets = [set(block) for block in universe.blocks]
        for size in range(1, universe.t):
            lower = schonheim_bound(universe.v - size, universe.k - size, universe.t - size)
            for subset in combinations(range(1, universe.v + 1), size):
                link = set(subset)
                fixed = sum(link <= block_sets[i] for i in retained)
                model.Add(sum(variables[i] for i in candidates if link <= block_sets[i])
                          + fixed >= lower)
    core_terms = [variables[i] for i in sorted(core - retained)]
    fixed_core = len(core & retained)
    if core_cap is not None:
        model.Add(sum(core_terms) + fixed_core <= core_cap)
    old_terms = [variables[i] for i in sorted(removed)]
    # Exact lexicographic objective: holes, core overlap, old blocks restored.
    core_weight = len(removed) + 1
    hole_weight = (len(core) + 1) * core_weight
    model.Minimize(hole_weight * sum(missing.values())
                   + core_weight * sum(core_terms) + sum(old_terms))
    for i, variable in variables.items():
        model.AddHint(variable, int(i in removed))
    old_coverage = {t for i in removed for t in universe.coverage[i]}
    for triple, variable in missing.items():
        model.AddHint(variable, int(triple not in old_coverage))
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 2
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.random_seed = seed % 2_147_483_647
    # OR-Tools9.15 can abort in MinimizeL1DistanceWithHint on presolved
    # partial-cover controls; keep ordinary hints without optional repair.
    solver.parameters.repair_hint = False
    solver.parameters.hint_conflict_limit = 2000
    solver.parameters.log_search_progress = output is not None
    solver.parameters.log_to_stdout = False
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
        model.ExportToFile(str(output / "model.pbtxt"))
        with (output / "solver.log").open("w") as stream:
            solver.log_callback = lambda line: (stream.write(line + "\n"), stream.flush())
            status = solver.Solve(model)
    else:
        status = solver.Solve(model)
    result = {"status": solver.StatusName(status), "solver_seconds": solver.WallTime(),
              "seed": seed, "requested_seconds": seconds, "workers": 2,
              "retained_ids": sorted(retained), "removed_ids": sorted(removed),
              "core_cap": core_cap, "max_missing": max_missing,
              "full_link_bounds": full_link_bounds,
              "deficient_after_removal": len(missing), "candidate_count": len(candidates),
              "objective_bound": solver.BestObjectiveBound(),
              "scope": "restricted partial-cover heuristic; no global infeasibility inference",
              "response_stats": solver.ResponseStats(), "selected_ids": None}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        witness = retained | {i for i in candidates if solver.Value(variables[i])}
        checked = verify_cover([universe.blocks[i] for i in sorted(witness)],
                               universe.v, universe.k, universe.t)
        uncovered = len(checked["uncovered"])
        if len(witness) != len(selected) or uncovered != sum(solver.Value(x)
                                                           for x in missing.values()):
            raise RuntimeError("solver witness disagrees with package verification")
        if core_cap is not None and len(witness & core) > core_cap:
            raise RuntimeError("solver witness exceeds the requested core cap")
        result.update(selected_ids=sorted(witness), uncovered=uncovered,
                      core_overlap=len(witness & core), changed_blocks=len(selected - witness),
                      objective=solver.ObjectiveValue(), package_verification=checked)
    return result


def choose_removed(universe, selected, core, rng, size, mode):
    selected = sorted(selected)
    if size >= len(selected):
        return selected
    counts = [0] * len(universe.triples)
    for i in selected:
        for t in universe.coverage[i]:
            counts[t] += 1
    holes = [universe.triples[t] for t, count in enumerate(counts) if not count]
    focus = set(rng.choice(holes)) if holes else set()
    ranking = []
    for i in selected:
        weight = 1.0
        if mode == "core":
            weight += 6 * (i in core)
        elif mode == "hole":
            weight += len(focus & set(universe.blocks[i])) ** 3
        elif mode == "redundant":
            weight += sum(counts[t] - 1 for t in universe.coverage[i])
        ranking.append((rng.random() ** (1 / weight), i))
    return sorted(i for _, i in sorted(ranking, reverse=True)[:size])


def check_state(path, universe, expected_count):
    blocks = read_blocks(path, universe.v, universe.k)
    report = verify_cover(blocks, universe.v, universe.k, universe.t)
    command = [sys.executable, str(Path(__file__).with_name("check_cover.py")), str(path),
               "--v", str(universe.v), "--k", str(universe.k), "--t", str(universe.t)]
    run = subprocess.run(command, capture_output=True, text=True, check=False)
    independent = json.loads(run.stdout)
    if (len(blocks) != expected_count or independent["blocks"] != expected_count
            or independent["uncovered_count"] != len(report["uncovered"])
            or bool(independent["valid"]) != bool(report["valid"])
            or {tuple(x) for x in independent["uncovered"]}
            != {tuple(x) for x in report["uncovered"]}
            or run.returncode not in (0, 1)):
        raise RuntimeError("package and independent checks disagree")
    return {"package": report, "standalone": independent}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("witness", type=Path)
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=600)
    parser.add_argument("--slice-seconds", type=float, default=15)
    parser.add_argument("--seed", type=int, default=2026101000)
    parser.add_argument("--max-missing", type=int, default=6)
    parser.add_argument("--full-link-bounds", action="store_true")
    args = parser.parse_args(argv)
    if any(not math.isfinite(x) or x <= 0 for x in (args.seconds, args.slice_seconds)):
        parser.error("time budgets must be finite and positive")
    universe = Universe.build()
    lookup = {b: i for i, b in enumerate(universe.blocks)}
    blocks = read_blocks(args.witness)
    baseline = frozenset(lookup[b] for b in blocks)
    if len(baseline) != 64 or len(blocks) != 64:
        parser.error("input must contain exactly64 distinct blocks")
    raw = args.core.read_bytes()
    core_data = json.loads(gzip.decompress(raw) if args.core.suffix == ".gz" else raw)
    core = frozenset(lookup[tuple(b)] for b in core_data["core_blocks"])
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "source_snapshot.py").write_bytes(Path(__file__).read_bytes())
    (args.output / "input.txt").write_bytes(args.witness.read_bytes())
    initial = check_state(args.output / "input.txt", universe, 64)
    initial_score = initial["standalone"]["uncovered_count"]
    initial_core = len(baseline & core)
    metadata = {"seed": args.seed, "seconds": args.seconds,
                "slice_seconds": args.slice_seconds, "workers": 2,
                "sizes": [12, 16, 20, 24, 28], "max_missing": args.max_missing,
                "full_link_bounds": args.full_link_bounds,
                "solver_version": ortools.__version__, "initial_uncovered": initial_score,
                "initial_core_overlap": initial_core, "initial_verification": initial,
                "source_revision": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True).strip(),
                "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "input_sha256": hashlib.sha256(args.witness.read_bytes()).hexdigest(),
                "core_input_sha256": hashlib.sha256(raw).hexdigest(),
                "core_ids": sorted(core),
                "overlap_definitions": {
                    "core_overlap": "shared blocks with the specified60-block rigid core",
                    "baseline_overlap": "shared blocks with the initial64-block near-cover seed"},
                "scope": "heuristic only; explicit neighborhood and core restrictions"}
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    rng = random.Random(args.seed)
    current = baseline
    best_score = initial_score
    best_core = initial_core
    archive = {digest_ids(baseline): (initial_score, initial_core, baseline)}
    seen = set(archive)
    near_states = []
    started = time.monotonic()
    attempt = 0
    with (args.output / "attempts.jsonl").open("w") as logs:
        while time.monotonic() - started < args.seconds:
            if attempt and attempt % 8 == 0:
                current = rng.choice(list(archive.values()))[2]
            size = metadata["sizes"][attempt % 5]
            escape = attempt % 2 == 1
            mode = ("core" if escape else ["hole", "redundant", "random"][attempt // 2 % 3])
            removed = choose_removed(universe, current, core, rng, size, mode)
            cap = max(0, len(current & core) - (2 if attempt % 4 == 3 else 1)) if escape else None
            folder = args.output / f"attempt-{attempt:04}"
            remaining = args.seconds - (time.monotonic() - started)
            result = solve_step(universe, current, removed, core,
                                min(args.slice_seconds, remaining),
                                args.seed + attempt, args.max_missing, cap, folder,
                                args.full_link_bounds)
            result.update(attempt=attempt, removal_mode=mode, escape=escape)
            ids = result["selected_ids"]
            if ids is not None:
                state = frozenset(ids)
                key = digest_ids(state)
                result.update(state_sha256=key, baseline_overlap=len(state & baseline),
                              novel=key not in seen)
                path = folder / "candidate.txt"
                write_blocks(path, [universe.blocks[i] for i in sorted(state)])
                checked = check_state(path, universe, 64)
                (folder / "verification.json").write_text(json.dumps(checked, indent=2) + "\n")
                if key not in seen:
                    seen.add(key)
                    archive[key] = (result["uncovered"], result["core_overlap"], state)
                    def rank(item):
                        return (item[1][0] + 0.35 * (item[1][1] - initial_core),
                                item[1][0], item[1][1])
                    archive = dict(sorted(archive.items(), key=rank)[:24])
                    if result["uncovered"] <= initial_score:
                        near_states.append({"attempt": attempt, "sha256": key,
                                            "uncovered": result["uncovered"],
                                            "core_overlap": result["core_overlap"],
                                            "baseline_overlap": result["baseline_overlap"]})
                current = state
                best_score = min(best_score, result["uncovered"])
                best_core = min(best_core, result["core_overlap"])
            (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")
            logs.write(json.dumps(result) + "\n")
            logs.flush()
            print(json.dumps({k: result.get(k) for k in
                              ("attempt", "status", "uncovered", "core_overlap", "changed_blocks",
                               "baseline_overlap", "novel", "escape")}), flush=True)
            attempt += 1
            if result.get("uncovered") == 0:
                break
    summary = {"attempts": attempt, "elapsed_seconds": time.monotonic() - started,
               "best_uncovered": best_score, "minimum_core_overlap": best_core,
               "distinct_states": len(seen), "new_near_states": near_states,
               "scope": "bounded heuristic; no global bound or infeasibility claim"}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
