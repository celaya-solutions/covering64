#!/usr/bin/env python3
# Document:    Alternating Regular Link and Outside Block Search
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Coordinate descent on bounded family pools, alternating with outside CP repair."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import random
import subprocess
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

from covering64.core import Universe, read_blocks, verify_cover, write_blocks

spec = importlib.util.spec_from_file_location(
    "r4_links", Path(__file__).with_name("r4_link_search.py"))
r4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r4)
links = r4.links


def family_data(family, triples, pairs):
    missing = links.check_template(family)
    covered = {t for b in family for t in combinations(b, 3)}
    pair_counts = Counter(p for b in family for p in combinations(b, 2))
    if max(pair_counts.values()) > 2:
        raise ValueError("unexpected triple pair multiplicity in family")
    return {"triple_mask": sum(1 << triples[t] for t in covered),
            "pair_one": sum(1 << pairs[p] for p, n in pair_counts.items() if n >= 1),
            "pair_two": sum(1 << pairs[p] for p, n in pair_counts.items() if n >= 2),
            "pair_counts": [pair_counts[p] for p in pairs],
            "spokes": int((0, 1) in missing) + 2 * int((0, 2) in missing)}


def choose_families(selected, family_stats, outside, triples, pairs, rng):
    selected = selected.copy()
    outside_mask = sum(1 << triples[t] for t in {
        t for b in outside for t in combinations(b, 3)})
    outside_pairs = Counter(p for b in outside for p in combinations(b, 2))
    all_mask = (1 << len(triples)) - 1
    history = []
    # Keep the first family fixed; update the other two, preserving every pair lower bound.
    for _ in range(8):
        changed = False
        for which in (1, 2):
            other = [family_stats[selected[i]] for i in range(3) if i != which]
            covered = outside_mask | other[0]["triple_mask"] | other[1]["triple_mask"]
            residual = all_mask ^ covered
            needed_one = needed_two = 0
            for pair, index in pairs.items():
                needed = (5 - outside_pairs[pair] - int(pair in links.EDGES)
                          - other[0]["pair_counts"][index] - other[1]["pair_counts"][index])
                if needed > 2:
                    raise ValueError("no family can preserve the pair bounds")
                if needed >= 1:
                    needed_one |= 1 << index
                if needed >= 2:
                    needed_two |= 1 << index
            other_spokes = other[0]["spokes"] | other[1]["spokes"]
            best_score = (family_stats[selected[which]]["triple_mask"] & residual).bit_count()
            choices = [selected[which]]
            for index, row in enumerate(family_stats):
                if ((row["pair_one"] & needed_one) != needed_one
                        or (row["pair_two"] & needed_two) != needed_two
                        or (row["spokes"] | other_spokes) != 3):
                    continue
                score = (row["triple_mask"] & residual).bit_count()
                if score > best_score:
                    best_score, choices = score, [index]
                elif score == best_score:
                    choices.append(index)
            replacement = rng.choice(choices)
            changed |= replacement != selected[which]
            selected[which] = replacement
        covered = outside_mask
        for index in selected:
            covered |= family_stats[index]["triple_mask"]
        history.append({"families": selected.copy(), "holes": (all_mask ^ covered).bit_count()})
        if not changed or sum(row["families"] == selected for row in history) > 1:
            break
    return selected, history


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r4-template", type=Path, required=True)
    parser.add_argument("--r6-template", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=2026101900)
    parser.add_argument("--samples", type=int, default=2000)
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--seconds", type=float, default=5)
    args = parser.parse_args()
    if args.output.exists() or args.samples < 1 or args.rounds < 1 or args.seconds <= 0:
        parser.error("fresh output and positive budgets required")
    rng = random.Random(args.seed)
    templates = [tuple(tuple(p - 1 for p in b) for b in read_blocks(path, v=13, k=4))
                 for path in (args.r4_template, args.r6_template)]
    seeds = []
    pool = set()
    for path in args.candidate:
        blocks = read_blocks(path)
        checked = verify_cover(blocks)
        if len(blocks) != 64 or set(checked["replication"].values()) != {20}:
            raise ValueError("seed is not a64-block regular20 partial candidate")
        selected = [tuple(sorted(tuple(p - 4 for p in block if p >= 4) for block in blocks
                                 if anchor in block and sum(p <= 3 for p in block) == 1))
                    for anchor in (1, 2, 3)]
        for family in selected:
            links.check_template(family)
            pool.add(family)
        seeds.append((path, blocks, selected))
    for template in templates:
        for leaf in (1, 2):
            for _ in range(args.samples):
                pool.add(links.mapped(template, r4.compatible_map(template, leaf, rng)))
    plane = links.projective_plane()
    for _ in range(args.samples):
        pool.add(links.mapped(plane, links.random_map("pg", 1, rng)))
    families = sorted(pool)
    triples = {t: i for i, t in enumerate(combinations(range(13), 3))}
    pairs = {p: i for i, p in enumerate(combinations(range(13), 2))}
    stats = [family_data(f, triples, pairs) for f in families]
    universe = Universe.build()
    block_ranks = {b: i for i, b in enumerate(universe.blocks)}
    args.output.mkdir(parents=True)
    pool_raw = gzip.compress((json.dumps(families, separators=(",", ":")) + "\n").encode(), mtime=0)
    (args.output / "pool.json.gz").write_bytes(pool_raw)
    metadata = {"seed": args.seed, "samples_per_template_leaf": args.samples,
                "pg_samples": args.samples, "pool_size": len(families), "rounds": args.rounds,
                "solver_version": links.ortools.__version__, "workers": 2,
                "solver_seconds_per_round": args.seconds,
                "seed_candidates": [{"path": str(path),
                                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                                    for path in args.candidate],
                "pool_sha256": hashlib.sha256(pool_raw).hexdigest(),
                "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                          text=True).strip(),
                "scope": "Bounded sampled families, first link fixed within each restart"}
    for name, path in (("source", Path(__file__)), ("r4-helper", Path(r4.__file__)),
                       ("solver-helper", Path(links.__file__))):
        raw = path.read_bytes()
        (args.output / f"{name}.py").write_bytes(raw)
        metadata[f"{name}_sha256"] = hashlib.sha256(raw).hexdigest()
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    summary = []
    for restart, (_, blocks, initial) in enumerate(seeds):
        selected = [families.index(f) for f in initial]
        outside_ids = [block_ranks[b] for b in blocks if min(b) >= 4]
        for round_number in range(args.rounds):
            outside = [tuple(p - 4 for p in universe.blocks[i]) for i in outside_ids]
            selected, response = choose_families(selected, stats, outside, triples, pairs, rng)
            fixed = links.fixed_blocks([families[i] for i in selected], [list(range(13))] * 3)
            candidate = sorted(list(fixed) + [universe.blocks[i] for i in outside_ids])
            folder = args.output / f"restart-{restart}-round-{round_number}"
            write_blocks(folder / "link-response.txt", candidate)
            checked = verify_cover(candidate)
            if min(checked["pair_multiplicities"]) < 5:
                raise RuntimeError("link response violated pair bounds")
            run = subprocess.run([sys.executable, "scripts/check_cover.py",
                                  str(folder / "link-response.txt"), "--expected-blocks", "64"],
                                 capture_output=True, text=True, check=False)
            standalone = json.loads(run.stdout)
            if (standalone["uncovered_count"] != len(checked["uncovered"])
                    or standalone["canonical_sha256"] != checked["canonical_sha256"]):
                raise RuntimeError("link response standalone verification disagrees")
            (folder / "link-response.json").write_text(json.dumps({
                "selected_families": selected, "response": response,
                "package": checked, "standalone": standalone},
                indent=2) + "\n")
            result = links.complete(fixed, args.seconds,
                                    args.seed + 100 * restart + round_number, folder,
                                    minimize_uncovered=True, hint_outside_ids=outside_ids)
            if result.get("candidate"):
                outside_ids = [block_ranks[tuple(b)] for b in result["candidate"] if min(b) >= 4]
            summary.append({"restart": restart, "round": round_number,
                            "link_response_holes": len(checked["uncovered"]),
                            "status": result["status"], "holes": result.get("holes"),
                            "solver_seconds": result["solver_seconds"]})
            (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
            print(json.dumps(summary[-1]), flush=True)
            if result["witness"]:
                return


if __name__ == "__main__":
    main()
