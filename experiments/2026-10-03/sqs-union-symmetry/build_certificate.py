#!/usr/bin/env python3
# Document:    SQS Union Pool Carrier Symmetry Certificate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Enumerate affine automorphisms; no solver or new covering model is created."""

import hashlib
import json
from collections import deque
from itertools import combinations, product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/new-construction-web-20261003"
IDENTITY = tuple(range(1, 17))
TARGET = (9, 10, 11)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transform(block, mapping):
    return tuple(sorted(mapping[p - 1] for p in block))


def closure(generators):
    group, queue = {IDENTITY}, deque([IDENTITY])
    while queue:
        current = queue.popleft()
        for g in generators:
            image = tuple(g[p - 1] for p in current)
            if image not in group:
                group.add(image)
                queue.append(image)
    return group


def affine_maps():
    maps = set()
    for first, second, fourth, shift in product(range(1, 8), range(1, 8), range(8, 16),
                                                range(8)):
        images = (first, second, 4, fourth)
        values = []
        for point in range(16):
            image = shift
            for bit in range(4):
                if point & (1 << bit):
                    image ^= images[bit]
            values.append(image + 1)
        if len(set(values)) == 16:
            maps.add(tuple(values))
    assert len(maps) == 1536
    return maps


def main():
    assert not (HERE / "certificate.json").exists(), "preserve completed certificate"
    seeds = [set(tuple(map(int, line.split())) for line in (RAW / name).read_text().splitlines())
             for name in ("sqs16-affine.txt", "sqs16-traded.txt")]
    payload = json.loads((RAW / "union-pool.json").read_text())
    pool = [tuple(row["block"]) for row in payload["pool"]]
    family = set(pool)
    group = affine_maps()
    for g in group:
        assert sorted(g) == list(IDENTITY)
        assert all({transform(b, g) for b in seed} == seed for seed in seeds)
        assert {transform(b, g) for b in family} == family
    generators, generated = [], {IDENTITY}
    for g in sorted(group):
        if g not in generated:
            generators.append(g)
            generated = closure(generators)
            assert generated <= group
    assert generated == group
    stabilizer = sorted(g for g in group if transform(TARGET, g) == TARGET)
    assert len(stabilizer) == 48
    carriers = sorted(b for b in pool if set(TARGET) <= set(b))
    assert len(carriers) == 30
    remaining, orbits = set(carriers), []
    while remaining:
        representative = min(remaining)
        orbit = {transform(representative, g) for g in stabilizer}
        assert orbit <= remaining
        members = []
        for block in sorted(orbit):
            mapping = next(g for g in stabilizer if transform(block, g) == representative)
            members.append({"block": block, "to_representative": mapping})
        orbits.append({"representative": representative, "size": len(orbit), "members": members})
        remaining -= orbit
    all_blocks = list(combinations(IDENTITY, 5))
    representatives = [orbit["representative"] for orbit in orbits]
    certificate = {
        "source_sha256": digest(Path(__file__)),
        "pool_sha256": digest(RAW / "union-pool.json"),
        "base_model_sha256": digest(RAW / "exact64-sqs-union.pbtxt"),
        "seed_sha256": {name: digest(RAW / name)
                        for name in ("sqs16-affine.txt", "sqs16-traded.txt")},
        "zero_based_group_description": "Affine maps x -> Lx+u with u in U={0,...,7}, "
            "L(U)=U and L(4)=4; all invertible such maps are enumerated.",
        "generators_images_of_1_to_16": generators, "group_order": len(group),
        "all_group_maps_explicitly_preserve_each_seed_and_pool": True,
        "target_triple": TARGET, "stabilizer_order": len(stabilizer),
        "carrier_blocks": carriers, "carrier_count": len(carriers), "orbits": orbits,
        "representative_local_ids": [pool.index(b) for b in representatives],
        "representative_global_ids": [all_blocks.index(b) for b in representatives],
        "proposed_or": "At least one of the six representative blocks is selected.",
        "scope": "Satisfiability-preserving representative restriction for this union pool. "
            "Every cover has some isomorphic image satisfying the OR; not every labeled cover "
            "must satisfy it. No invariant-cover assumption, new model, solver run or bound.",
        "solver_calls": 0,
    }
    (HERE / "certificate.json").write_text(json.dumps(certificate, indent=2) + "\n")
    print(json.dumps({k: v for k, v in certificate.items() if k not in (
        "orbits", "carrier_blocks", "generators_images_of_1_to_16")}), flush=True)


if __name__ == "__main__":
    main()
