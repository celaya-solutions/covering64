# Document:    Degree nineteen link hub classification and search
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Enumerate hub shapes and seek19-block pair-cover links; no global exclusion."""

import argparse
import hashlib
import json
import subprocess
import time
from collections import Counter
from itertools import combinations, permutations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model


def edge_action(edges, perm):
    return tuple(sorted(tuple(sorted((perm[a], perm[b]))) for a, b in edges))


def matchings(stubs):
    if not stubs:
        yield ()
        return
    first = stubs[0]
    used = set()
    for index in range(1, len(stubs)):
        second = stubs[index]
        if second in used:
            continue
        used.add(second)
        rest = stubs[1:index] + stubs[index + 1 :]
        for suffix in matchings(rest):
            yield tuple(sorted(((first, second),) + suffix))


def hub_shapes():
    """Canonical6-vertex colored graphs encode all six hub-containing blocks.

    Four repeated leaves give four distinct simple edges: a parallel edge
    would repeat a non-excess leaf pair. The ten other points each occupy one
    slot and their five excess pairs give multigraph edges, including loops.
    Quotienting by every permutation of the six blocks loses no hub shape.
    """
    perms = list(permutations(range(6)))
    edges = list(combinations(range(6), 2))
    unseen = set()
    for a_edges in combinations(edges, 4):
        degrees = Counter(v for edge in a_edges for v in edge)
        if max(degrees.values()) <= 3:
            unseen.add(a_edges)
    result = []
    while unseen:
        a_edges = min(unseen)
        orbit = {edge_action(a_edges, p) for p in perms}
        unseen.difference_update(orbit)
        autos = [p for p in perms if edge_action(a_edges, p) == a_edges]
        degrees = Counter(v for edge in a_edges for v in edge)
        stubs = tuple(v for v in range(6) for _ in range(3 - degrees[v]))
        b_reps = {min(edge_action(m, p) for p in autos) for m in set(matchings(stubs))}
        for b_edges in sorted(b_reps):
            blocks = [[2] for _ in range(6)]
            for leaf, (a, b) in enumerate(a_edges, 3):
                blocks[a].append(leaf)
                blocks[b].append(leaf)
            for pair, (a, b) in enumerate(b_edges):
                blocks[a].append(7 + 2 * pair)
                blocks[b].append(8 + 2 * pair)
            blocks = sorted(tuple(sorted(block)) for block in blocks)
            if any(len(set(block)) != 4 for block in blocks) or len(set(blocks)) != 6:
                raise RuntimeError("malformed hub shape")
            result.append(
                {
                    "a_edges": a_edges,
                    "b_edges": b_edges,
                    "a_orbit_size": len(orbit),
                    "a_automorphism_count": len(autos),
                    "hub_blocks": blocks,
                }
            )
    return sorted(result, key=lambda shape: (shape["a_edges"], shape["b_edges"]))


def pair_targets():
    excess = {(2, x) for x in range(3, 7)} | {(x, x + 1) for x in range(7, 17, 2)}
    return {pair: 1 + (pair in excess) for pair in combinations(range(2, 17), 2)}


def check_link(blocks):
    blocks = [tuple(block) for block in blocks]
    if len(blocks) != 19 or len(set(blocks)) != 19:
        raise ValueError("expected19 distinct link blocks")
    if any(
        len(b) != 4
        or tuple(sorted(set(b))) != b
        or any(type(x) is not int or not 2 <= x <= 16 for x in b)
        for b in blocks
    ):
        raise ValueError("malformed link block")
    actual = Counter(pair for b in blocks for pair in combinations(b, 2))
    if actual != pair_targets():
        raise ValueError("link pair multiplicities mismatch")
    return True


def residual_model(hub):
    target = pair_targets()
    fixed = Counter(pair for block in hub for pair in combinations(block, 2))
    if any(fixed[pair] > count for pair, count in target.items()):
        raise ValueError("hub shape exceeds pair targets")
    remaining = {pair: count - fixed[pair] for pair, count in target.items()}
    blocks = [
        b
        for b in combinations(range(3, 17), 4)
        if all(remaining[p] > 0 for p in combinations(b, 2))
    ]
    model = cp_model.CpModel()
    xs = [model.new_bool_var("quad_" + "_".join(map(str, b))) for b in blocks]
    support = {pair: [] for pair in remaining}
    for block, x in zip(blocks, xs):
        for pair in combinations(block, 2):
            support[pair].append(x)
    for pair, count in remaining.items():
        model.add(sum(support[pair]) == count)
    model.add(sum(xs) == 13)
    return model, xs, blocks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=2)
    parser.add_argument("--seed", type=int, default=2026101200)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    if args.seconds <= 0 or args.limit < 0 or args.seed < 0:
        parser.error("invalid budget, limit or seed")
    args.output.mkdir(parents=True, exist_ok=True)
    shapes = hub_shapes()
    source = Path(__file__).read_bytes()
    (args.output / "source.py").write_bytes(source)
    metadata = {
        "scope": "All hub shapes; bounded residual searches are inconclusive unless witnessed",
        "shape_count": len(shapes),
        "seconds_per_shape": args.seconds,
        "seed": args.seed,
        "solver_version": ortools.__version__,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "shapes": shapes,
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    counts = Counter()
    for index, shape in enumerate(shapes[: args.limit or len(shapes)]):
        model, xs, blocks = residual_model(shape["hub_blocks"])
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = args.seconds
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = args.seed + index
        start = time.monotonic()
        status = solver.solve(model)
        result = {
            "index": index,
            "seed": args.seed + index,
            "status": solver.status_name(status),
            "seconds": time.monotonic() - start,
            "residual_candidate_count": len(blocks),
            "link": None,
            "response_stats": solver.response_stats(),
            "proof_generated": False,
        }
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            link = sorted(shape["hub_blocks"] + [b for b, x in zip(blocks, xs) if solver.value(x)])
            check_link(link)
            result["link"] = link
        counts[result["status"]] += 1
        with (args.output / "results.jsonl").open("a") as stream:
            stream.write(json.dumps(result) + "\n")
        print(json.dumps({"case": index, "status": result["status"], "counts": counts}), flush=True)


if __name__ == "__main__":
    main()
