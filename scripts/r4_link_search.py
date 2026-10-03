#!/usr/bin/env python3
# Document:    Four Missing Pair Link Construction Search
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Search explicit r4/r6/PG templates without assuming a complete classification."""
import argparse
import hashlib
import importlib.util
import json
import math
import random
import subprocess
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

from covering64.core import read_blocks, verify_cover

spec = importlib.util.spec_from_file_location(
    "three_links", Path(__file__).with_name("three_link_search.py"))
links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(links)


def missing_matching(template):
    if (len(template) != 13 or len(set(template)) != 13
            or any(len(b) != 4 or tuple(sorted(set(b))) != b
                   or any(type(p) is not int or not 0 <= p < 13 for p in b)
                   for b in template)):
        raise ValueError("13 distinct blocks required")
    degrees = Counter(p for b in template for p in b)
    if any(degrees[p] != 4 for p in range(13)):
        raise ValueError("regular degree4 required")
    pairs = {p for b in template for p in combinations(b, 2)}
    missing = sorted(set(combinations(range(13), 2)) - pairs)
    if len({p for edge in missing for p in edge}) != 2 * len(missing):
        raise ValueError("missing pairs are not a matching")
    return missing


def compatible_map(template, leaf, rng):
    holes = missing_matching(template)
    if not holes:
        return links.random_map("pg", leaf, rng)
    if len(holes) > 6:
        raise ValueError("too many missing edges")
    source_edges = holes.copy()
    rng.shuffle(source_edges)
    targets = [(0, leaf), *rng.sample(list(links.EDGES[2:]), len(holes) - 1)]
    mapping = [None] * 13
    for (a, b), (x, y) in zip(source_edges, targets):
        if rng.randrange(2):
            x, y = y, x
        mapping[a], mapping[b] = x, y
    free_targets = [p for p in range(13) if p not in mapping]
    rng.shuffle(free_targets)
    for p, target in zip([p for p in range(13) if mapping[p] is None], free_targets):
        mapping[p] = target
    links.check_template(links.mapped(template, mapping))
    return mapping


def mutate(template, permutation, leaf, rng):
    holes = missing_matching(template)
    if not holes:
        return links.mutate(permutation, "pg", rng)
    move = rng.randrange(5)
    if move == 0:
        return compatible_map(template, leaf, rng)
    changed = permutation.copy()
    if move == 1:
        a, b = rng.choice(holes)
        changed[a], changed[b] = changed[b], changed[a]
    elif move == 2:
        free = sorted(set(range(13)) - {p for e in holes for p in e})
        if len(free) > 1:
            a, b = rng.sample(free, 2)
            changed[a], changed[b] = changed[b], changed[a]
    else:
        transform = list(range(13))
        if move == 3:
            a, b = rng.choice(links.EDGES[2:])
            transform[a], transform[b] = b, a
        else:
            first, second = rng.sample(list(links.EDGES[2:]), 2)
            for a, b in zip(first, second):
                transform[a], transform[b] = b, a
        changed = [transform[p] for p in changed]
    return changed


def optimize(templates, seconds, seed, keep):
    rng = random.Random(seed)
    triple_ids = {t: i for i, t in enumerate(combinations(range(13), 3))}

    def mask(template, permutation):
        return sum(1 << i for i in {triple_ids[t] for b in links.mapped(template, permutation)
                                   for t in combinations(b, 3)})

    start = time.monotonic()
    archive = {}
    iterations = 0
    best = 0
    while time.monotonic() - start < seconds:
        permutations = [compatible_map(template, 1 + i % 2, rng)
                        for i, template in enumerate(templates)]
        masks = [mask(t, p) for t, p in zip(templates, permutations)]
        score = (masks[0] | masks[1] | masks[2]).bit_count()
        for step in range(1200):
            if time.monotonic() - start >= seconds:
                break
            which = rng.randrange(3)
            proposal = mutate(templates[which], permutations[which], 1 + which % 2, rng)
            new_masks = masks.copy()
            new_masks[which] = mask(templates[which], proposal)
            new_score = (new_masks[0] | new_masks[1] | new_masks[2]).bit_count()
            temperature = 0.1 + 1.5 * (1 - step / 1200)
            if new_score >= score or rng.random() < math.exp((new_score - score) / temperature):
                permutations[which], masks, score = proposal, new_masks, new_score
            iterations += 1
            if score >= best:
                best = score
                archive[tuple(tuple(p) for p in permutations)] = {
                    "permutations": [p.copy() for p in permutations],
                    "outside_triples_covered": score, "iteration": iterations}
                if len(archive) > keep * 8:
                    archive = dict(sorted(archive.items(),
                                          key=lambda x: (-x[1]["outside_triples_covered"],
                                                         x[1]["iteration"]))[:keep * 4])
    return {"candidates": sorted(archive.values(),
                                  key=lambda x: (-x["outside_triples_covered"],
                                                 x["iteration"]))[:keep],
            "best": best, "iterations": iterations, "seconds": time.monotonic() - start,
            "seed": seed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r4-template", type=Path, required=True)
    parser.add_argument("--r6-template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=2026101800)
    parser.add_argument("--optimize-seconds", type=float, default=5)
    parser.add_argument("--solve-seconds", type=float, default=30)
    parser.add_argument("--per-family", type=int, default=1)
    args = parser.parse_args()
    if args.output.exists() or args.per_family < 1 or any(
            not math.isfinite(s) or s <= 0 for s in (args.optimize_seconds, args.solve_seconds)):
        parser.error("fresh output and positive finite budgets required")
    args.output.mkdir(parents=True)
    templates = {"pg": links.projective_plane()}
    metadata = {"seed": args.seed, "optimize_seconds": args.optimize_seconds,
                "solve_seconds": args.solve_seconds, "per_family": args.per_family,
                "solver_version": links.ortools.__version__, "workers": 2,
                "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                          text=True).strip(),
                "scope": "Bounded sampled r4/r6/PG template constructions only"}
    for label, path, expected in (("r4", args.r4_template, 4), ("r6", args.r6_template, 6)):
        blocks = read_blocks(path, v=13, k=4)
        report = verify_cover(blocks, 13, 4, 2)
        templates[label] = tuple(tuple(p - 1 for p in b) for b in blocks)
        if len(missing_matching(templates[label])) != expected:
            raise ValueError("unexpected number of template holes")
        metadata[label] = {"path": str(path),
                           "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                           "template": templates[label], "package": report}
    for label, path in (("source", Path(__file__)), ("helper", Path(links.__file__))):
        raw = path.read_bytes()
        (args.output / f"{label}.py").write_bytes(raw)
        metadata[f"{label}_sha256"] = hashlib.sha256(raw).hexdigest()
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    queue = []
    for number, names in enumerate((("pg", "r4", "r4"), ("r4", "r4", "r4"),
                                     ("r4", "r6", "r4"))):
        selected = [templates[name] for name in names]
        optimized = optimize(selected, args.optimize_seconds, args.seed + number, args.per_family)
        (args.output / f"optimized-{number}.json").write_text(
            json.dumps(optimized, indent=2) + "\n")
        print(json.dumps({"family": names, "best_union": optimized["best"]}), flush=True)
        queue.extend((names, selected, row) for row in optimized["candidates"])
    summary = []
    for number, (names, selected, row) in enumerate(queue):
        fixed = links.fixed_blocks(selected, row["permutations"])
        result = links.complete(fixed, args.solve_seconds, args.seed + 100 + number,
                                args.output / f"case-{number:03}", minimize_uncovered=True)
        summary.append({"case": number, "family": names, "status": result["status"],
                        "outside_triple_union": row["outside_triples_covered"],
                        "holes": result.get("holes"), "solver_seconds": result["solver_seconds"]})
        (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary[-1]), flush=True)
        if result["witness"]:
            break


if __name__ == "__main__":
    main()
