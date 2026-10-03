#!/usr/bin/env python3
# Document:    Three Regular Link Construction Search
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Bounded construction within three explicit regular13-quad link templates.

The seven blocks containing123 use outside edges45,46,78,...,15-16.
Each anchor has13 further blocks, whose outside4-blocks form a regular4 family
covering all outside pairs except possibly those seven edges. This closes all
triples touching123. The18 outside blocks have degree6 at4 and7 elsewhere,
so a completion is a regular20 cover. This template family is not exhaustive.
"""
import argparse
import hashlib
import json
import math
import random
import subprocess
import sys
import time
from collections import Counter
from itertools import combinations, product
from pathlib import Path

import ortools
from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model

from covering64.core import Universe, read_blocks, verify_cover, write_blocks


def projective_plane():
    points = [p for p in product(range(3), repeat=3)
              if any(p) and next(x for x in p if x) == 1]
    return tuple(sorted(tuple(i for i, p in enumerate(points)
                              if sum(a * b for a, b in zip(p, normal)) % 3 == 0)
                        for normal in points))


EDGES = ((0, 1), (0, 2)) + tuple((i, i + 1) for i in range(3, 13, 2))


def check_template(template):
    if (len(template) != 13 or len(set(template)) != 13
            or any(len(b) != 4 or tuple(sorted(set(b))) != b
                   or any(type(x) is not int or not 0 <= x < 13 for x in b)
                   for b in template)):
        raise ValueError("malformed13-quad template")
    degrees = Counter(x for b in template for x in b)
    if any(degrees[x] != 4 for x in range(13)):
        raise ValueError("template is not regular4")
    pairs = {pair for b in template for pair in combinations(b, 2)}
    missing = set(combinations(range(13), 2)) - pairs
    if not missing <= set(EDGES):
        raise ValueError("template leaves a pair outside seven fixed edges")
    return missing


def mapped(template, permutation):
    if sorted(permutation) != list(range(13)):
        raise ValueError("not a13-point permutation")
    return tuple(sorted(tuple(sorted(permutation[x] for x in b)) for b in template))


def fixed_blocks(templates, permutations):
    if len(templates) != 3 or len(permutations) != 3:
        raise ValueError("three links required")
    blocks = [(1, 2, 3, a + 4, b + 4) for a, b in EDGES]
    for anchor, template, permutation in zip((1, 2, 3), templates, permutations):
        link = mapped(template, permutation)
        check_template(link)
        blocks.extend((anchor, *(x + 4 for x in b)) for b in link)
    if len(set(blocks)) != 46:
        raise ValueError("fixed blocks are not46 distinct blocks")
    return tuple(sorted(blocks))


def random_map(kind, leaf, rng):
    if kind == "pg":
        permutation = list(range(13))
        rng.shuffle(permutation)
        return permutation
    # The nonplane source has holes01,34,56,78,9-10,11-12 and unmatched2.
    permutation = [None] * 13
    permutation[:3] = [0, leaf, 3 - leaf]
    if rng.randrange(2):
        permutation[0], permutation[1] = permutation[1], permutation[0]
    pairs = list(range(5))
    rng.shuffle(pairs)
    for source, target in enumerate(pairs):
        values = [3 + 2 * target, 4 + 2 * target]
        if rng.randrange(2):
            values.reverse()
        permutation[3 + 2 * source:5 + 2 * source] = values
    return permutation


def mutate(permutation, kind, rng):
    changed = permutation.copy()
    if kind == "pg":
        a, b = rng.sample(range(13), 2)
        changed[a], changed[b] = changed[b], changed[a]
    else:
        move = rng.randrange(3)
        if move == 0:
            changed[0], changed[1] = changed[1], changed[0]
        elif move == 1:
            a = 3 + 2 * rng.randrange(5)
            changed[a], changed[a + 1] = changed[a + 1], changed[a]
        else:
            a, b = [3 + 2 * x for x in rng.sample(range(5), 2)]
            changed[a:a + 2], changed[b:b + 2] = changed[b:b + 2], changed[a:a + 2]
    return changed


def optimize(templates, kinds, seconds, seed, keep):
    rng = random.Random(seed)
    triple_ids = {t: i for i, t in enumerate(combinations(range(13), 3))}

    def mask(template, permutation):
        return sum(1 << i for i in {triple_ids[t] for b in mapped(template, permutation)
                                   for t in combinations(b, 3)})

    start = time.monotonic()
    archive = {}
    iterations = 0
    best = 0
    while time.monotonic() - start < seconds:
        permutations = [random_map(kind, 1 + (i % 2), rng)
                        for i, kind in enumerate(kinds)]
        masks = [mask(t, p) for t, p in zip(templates, permutations)]
        score = (masks[0] | masks[1] | masks[2]).bit_count()
        for step in range(1500):
            if time.monotonic() - start >= seconds:
                break
            which = rng.randrange(3)
            proposal = mutate(permutations[which], kinds[which], rng)
            proposal_mask = mask(templates[which], proposal)
            new_masks = masks.copy()
            new_masks[which] = proposal_mask
            new_score = (new_masks[0] | new_masks[1] | new_masks[2]).bit_count()
            temperature = 0.12 + 1.5 * (1 - step / 1500)
            if new_score >= score or rng.random() < math.exp((new_score - score) / temperature):
                permutations[which] = proposal
                masks = new_masks
                score = new_score
            iterations += 1
            if score >= best:
                best = score
                key = tuple(tuple(p) for p in permutations)
                archive[key] = {"permutations": [p.copy() for p in permutations],
                                "outside_triples_covered": score,
                                "iteration": iterations}
                if len(archive) > keep * 8:
                    ranked = sorted(archive.items(),
                                    key=lambda x: (-x[1]["outside_triples_covered"],
                                                   x[1]["iteration"]))
                    archive = dict(ranked[:keep * 4])
    values = sorted(archive.values(), key=lambda x: (-x["outside_triples_covered"],
                                                     x["iteration"]))[:keep]
    return {"candidates": values, "iterations": iterations,
            "seconds": time.monotonic() - start, "best": best, "seed": seed}


def complete(fixed, seconds, seed, output, minimize_uncovered=False, hint_outside_ids=None):
    universe = Universe.build()
    fixed_ids = [universe.blocks.index(b) for b in fixed]
    covered = {t for b in fixed_ids for t in universe.coverage[b]}
    missing = sorted(set(range(560)) - covered)
    if any(set(universe.triples[t]) & {1, 2, 3} for t in missing):
        raise ValueError("fixed links are not closed")
    candidates = [i for i, b in enumerate(universe.blocks) if min(b) >= 4]
    model = cp_model.CpModel()
    variables = {i: model.NewBoolVar(f"block_{i}") for i in candidates}
    model.Add(sum(variables.values()) == 18)
    uncovered = []
    for tid in missing:
        coverage = sum(variables[i] for i in universe.containing[tid] if i in variables)
        if minimize_uncovered:
            hole = model.NewBoolVar(f"uncovered_{tid}")
            model.Add(coverage == 0).OnlyEnforceIf(hole)
            model.Add(coverage >= 1).OnlyEnforceIf(hole.Not())
            uncovered.append(hole)
        else:
            model.Add(coverage >= 1)
    if uncovered:
        model.Minimize(sum(uncovered))
    for point in range(4, 17):
        model.Add(sum(variables[i] for i in candidates if point in universe.blocks[i])
                  == (6 if point == 4 else 7))
    for pair in combinations(range(4, 17), 2):
        count = sum(set(pair) <= set(block) for block in fixed)
        model.Add(sum(variables[i] for i in candidates if set(pair) <= set(universe.blocks[i]))
                  + count >= 5)
    # A relaxation including the fixed degree equations screens only this construction.
    lp = pywraplp.Solver.CreateSolver("GLOP")
    lp_vars = {i: lp.NumVar(0, 1, f"block_{i}") for i in candidates}
    for tid in missing:
        lp.Add(sum(lp_vars[i] for i in universe.containing[tid] if i in lp_vars) >= 1)
    for point in range(4, 17):
        lp.Add(sum(lp_vars[i] for i in candidates if point in universe.blocks[i])
               == (6 if point == 4 else 7))
    lp.Minimize(sum(lp_vars.values()))
    lp_status = lp.Solve()
    if hint_outside_ids is not None:
        if (len(hint_outside_ids) != 18 or len(set(hint_outside_ids)) != 18
                or not set(hint_outside_ids) <= set(candidates)):
            raise ValueError("hint must contain18 distinct outside block IDs")
        hinted = set(hint_outside_ids)
        for i in candidates:
            model.AddHint(variables[i], int(i in hinted))
        for tid, variable in zip(missing, uncovered):
            model.AddHint(variable, int(not any(i in hinted for i in universe.containing[tid])))
    elif lp_status == pywraplp.Solver.OPTIMAL:
        for i in candidates:
            model.AddHint(variables[i], int(lp_vars[i].solution_value() > 0.5))
    output.mkdir(parents=True, exist_ok=True)
    write_blocks(output / "fixed.txt", fixed)
    model.ExportToFile(str(output / "model.pbtxt"))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = 2
    solver.parameters.random_seed = seed % 2_147_483_647
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    improvements = []

    class SaveImprovement(cp_model.CpSolverSolutionCallback):
        def on_solution_callback(self):
            holes = sum(self.Value(variable) for variable in uncovered)
            if improvements and holes >= improvements[-1]["holes"]:
                return
            witness = sorted(list(fixed) + [universe.blocks[i] for i in candidates
                                            if self.Value(variables[i])])
            checked = verify_cover(witness)
            if len(witness) != 64 or len(checked["uncovered"]) != holes:
                raise RuntimeError("improvement failed package verification")
            folder = output / "improvements"
            path = folder / f"candidate-{len(improvements):03}.txt"
            write_blocks(path, witness)
            run = subprocess.run([sys.executable, "scripts/check_cover.py", str(path),
                                  "--expected-blocks", "64"],
                                 capture_output=True, text=True, check=False)
            standalone = json.loads(run.stdout)
            if (standalone["uncovered_count"] != holes
                    or standalone["canonical_sha256"] != checked["canonical_sha256"]):
                raise RuntimeError("improvement failed standalone verification")
            improvements.append({"holes": holes, "solver_seconds": self.WallTime(),
                                 "path": str(path), "package": checked,
                                 "standalone": standalone})
            (folder / "index.json").write_text(json.dumps(improvements, indent=2) + "\n")

    with (output / "solver.log").open("w") as stream:
        solver.log_callback = lambda line: (stream.write(line + "\n"), stream.flush())
        status = solver.Solve(model, SaveImprovement())
    result = {"status": solver.StatusName(status), "solver_seconds": solver.WallTime(),
              "seconds_budget": seconds, "seed": seed, "workers": 2,
              "lp_status": lp_status, "missing_outside_triples": len(missing),
              "candidate_count": len(candidates), "fixed_block_ids": fixed_ids,
              "model_sha256": hashlib.sha256((output / "model.pbtxt").read_bytes()).hexdigest(),
              "response_stats": solver.ResponseStats(), "witness": None,
              "minimize_uncovered": minimize_uncovered,
              "hint_outside_ids": hint_outside_ids,
              "scope": "This three-link construction only; no exhaustive or global inference"}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        witness = sorted(list(fixed) + [universe.blocks[i] for i in candidates
                                       if solver.Value(variables[i])])
        checked = verify_cover(witness)
        holes = len(checked["uncovered"])
        if len(witness) != 64 or (not minimize_uncovered and holes):
            raise RuntimeError("package verification failed")
        if uncovered and holes != sum(solver.Value(variable) for variable in uncovered):
            raise RuntimeError("objective and verifier hole count disagree")
        write_blocks(output / "candidate.txt", witness)
        run = subprocess.run([sys.executable, "scripts/check_cover.py",
                              str(output / "candidate.txt"), "--expected-blocks", "64"],
                             capture_output=True, text=True, check=False)
        standalone = json.loads(run.stdout)
        if (standalone["uncovered_count"] != holes or standalone["valid"] != checked["valid"]
                or standalone["canonical_sha256"] != checked["canonical_sha256"]):
            raise RuntimeError("standalone verification failed")
        result.update(witness=witness if not holes else None, candidate=witness, holes=holes,
                      package=checked, standalone=standalone)
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spoke-template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=2026101500)
    parser.add_argument("--optimize-seconds", type=float, default=15)
    parser.add_argument("--solve-seconds", type=float, default=30)
    parser.add_argument("--per-family", type=int, default=4)
    parser.add_argument("--minimize-uncovered", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("refusing to overwrite an existing campaign")
    if args.per_family < 1 or any(not math.isfinite(s) or s <= 0
                                for s in (args.optimize_seconds, args.solve_seconds)):
        parser.error("positive finite budgets and candidate counts required")
    pg = projective_plane()
    spoke = tuple(sorted(tuple(x - 1 for x in b)
                         for b in read_blocks(args.spoke_template, v=13, k=4)))
    if check_template(pg) or check_template(spoke) != {(0, 1), *EDGES[2:]}:
        raise ValueError("unexpected template pair holes")
    args.output.mkdir(parents=True)
    source = Path(__file__).read_bytes()
    (args.output / "source.py").write_bytes(source)
    metadata = {"source_sha256": hashlib.sha256(source).hexdigest(),
                "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                          text=True).strip(),
                "spoke_source_sha256": hashlib.sha256(args.spoke_template.read_bytes()).hexdigest(),
                "spoke_template": spoke, "projective_plane": pg,
                "ortools_version": ortools.__version__,
                "seed": args.seed, "optimize_seconds_per_family": args.optimize_seconds,
                "solve_seconds_per_case": args.solve_seconds, "per_family": args.per_family,
                "minimize_uncovered": args.minimize_uncovered,
                "scope": "Heuristic template construction, not a complete link classification"}
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    queue = []
    families = [("pg", "pg", "pg"), ("pg", "spoke", "spoke"), ("spoke", "spoke", "spoke")]
    for index, kinds in enumerate(families):
        templates = [pg if kind == "pg" else spoke for kind in kinds]
        optimized = optimize(templates, kinds, args.optimize_seconds,
                             args.seed + index, args.per_family)
        (args.output / f"optimized-{index}.json").write_text(json.dumps(optimized, indent=2) + "\n")
        print(json.dumps({"family": kinds, "best_union": optimized["best"],
                          "iterations": optimized["iterations"]}), flush=True)
        queue.extend((index, kinds, templates, candidate) for candidate in optimized["candidates"])
    summary = []
    for number, (index, kinds, templates, candidate) in enumerate(queue):
        fixed = fixed_blocks(templates, candidate["permutations"])
        result = complete(fixed, args.solve_seconds, args.seed + 100 + number,
                          args.output / f"case-{number:03}", args.minimize_uncovered)
        summary.append({"case": number, "family": kinds, "family_index": index,
                        "outside_triple_union": candidate["outside_triples_covered"],
                        "status": result["status"], "solver_seconds": result["solver_seconds"]})
        summary[-1]["holes"] = result.get("holes")
        (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary[-1]), flush=True)
        if result["witness"]:
            break


if __name__ == "__main__":
    main()
