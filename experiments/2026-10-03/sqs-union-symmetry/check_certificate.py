#!/usr/bin/env python3
# Document:    Independent SQS Carrier Symmetry Certificate Checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Replay generator closure and every carrier map; never build or solve a model."""

import copy
import hashlib
import json
from collections import Counter, deque
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/new-construction-web-20261003"
IDENTITY = tuple(range(1, 17))
TARGET = (9, 10, 11)
POOL_HASH = "b1e0e13ac3787643b25e920d2ce8f83d7119dedcb3c78daaf8316e04510c68c6"
MODEL_HASH = "d0a70c16b53c2399ed10eae2deb77b3c817e352a4fc950d7584291b3c249703f"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relabel(block, mapping):
    return tuple(sorted(mapping[label - 1] for label in block))


def affine_conditions(mapping):
    assert len(mapping) == 16 and tuple(sorted(mapping)) == IDENTITY
    shift = mapping[0] - 1
    assert 0 <= shift < 8
    linear = tuple((value - 1) ^ shift for value in mapping)
    assert linear[0] == 0 and linear[4] == 4 and set(linear[:8]) == set(range(8))
    assert all(linear[x ^ y] == linear[x] ^ linear[y] for x in range(16) for y in range(16))


def group_from_generators(generators, seeds, family):
    for generator in generators:
        affine_conditions(generator)
        assert all({relabel(block, generator) for block in seed} == seed for seed in seeds)
        assert {relabel(block, generator) for block in family} == family
    found, pending = {IDENTITY}, deque([IDENTITY])
    while pending:
        current = pending.pop()
        for generator in generators:
            composed = tuple(current[point - 1] for point in generator)
            if composed not in found:
                found.add(composed)
                assert len(found) <= 1536
                pending.append(composed)
    assert len(found) == 1536
    # A finite composition-closed semigroup of permutations containing identity
    # is a group; inverse membership is also checked directly for every map.
    assert all(tuple(g.index(point) + 1 for point in IDENTITY) in found for g in found)
    return found


def inspect(data, seeds, pool):
    assert data["pool_sha256"] == POOL_HASH and data["base_model_sha256"] == MODEL_HASH
    assert data["source_sha256"] == sha(HERE / "build_certificate.py")
    assert data["solver_calls"] == 0
    assert data["all_group_maps_explicitly_preserve_each_seed_and_pool"] is True
    assert data["group_order"] == 1536 and data["target_triple"] == list(TARGET)
    for name in ("sqs16-affine.txt", "sqs16-traded.txt"):
        assert data["seed_sha256"][name] == sha(RAW / name)
    group = group_from_generators(data["generators_images_of_1_to_16"], seeds, set(pool))
    stabilizer = {g for g in group if set(g[p - 1] for p in TARGET) == set(TARGET)}
    assert len(stabilizer) == data["stabilizer_order"] == 48
    carriers = sorted(block for block in pool if all(point in block for point in TARGET))
    assert data["carrier_count"] == len(carriers) == 30
    assert data["carrier_blocks"] == [list(block) for block in carriers]
    assert len(data["orbits"]) == 6
    seen, representatives, sizes = set(), [], []
    for row in data["orbits"]:
        representative = tuple(row["representative"])
        orbit = {relabel(representative, g) for g in stabilizer}
        assert representative == min(orbit) and orbit <= set(carriers)
        assert not seen & orbit and len(orbit) == row["size"]
        assert [tuple(member["block"]) for member in row["members"]] == sorted(orbit)
        for member in row["members"]:
            mapping = tuple(member["to_representative"])
            assert mapping in stabilizer
            assert relabel(tuple(member["block"]), mapping) == representative
        representatives.append(representative)
        sizes.append(len(orbit))
        seen.update(orbit)
    assert seen == set(carriers) and representatives == sorted(representatives)
    assert sizes == [12, 8, 3, 1, 3, 3]
    universe = list(combinations(IDENTITY, 5))
    assert data["representative_local_ids"] == [pool.index(b) for b in representatives]
    assert data["representative_global_ids"] == [universe.index(b) for b in representatives]
    return group, stabilizer, representatives


def main():
    checked = [HERE / "certificate.json", HERE / "build_certificate.py",
               RAW / "union-pool.json", RAW / "exact64-sqs-union.pbtxt",
               RAW / "sqs16-affine.txt", RAW / "sqs16-traded.txt"]
    before = {str(p.relative_to(ROOT)): sha(p) for p in checked}
    assert sha(RAW / "union-pool.json") == POOL_HASH
    assert sha(RAW / "exact64-sqs-union.pbtxt") == MODEL_HASH
    seeds = []
    for name in ("sqs16-affine.txt", "sqs16-traded.txt"):
        blocks = [tuple(map(int, line.split())) for line in (RAW / name).read_text().splitlines()]
        assert len(blocks) == len(set(blocks)) == 140
        assert all(len(b) == 4 and tuple(sorted(set(b))) == b and set(b) <= set(IDENTITY)
                   for b in blocks)
        counts = Counter(t for block in blocks for t in combinations(block, 3))
        assert counts == Counter({t: 1 for t in combinations(IDENTITY, 3)})
        seeds.append(set(blocks))
    all_quads = seeds[0] | seeds[1]
    pool = [b for b in combinations(IDENTITY, 5)
            if any(q in all_quads for q in combinations(b, 4))]
    saved_pool = json.loads((RAW / "union-pool.json").read_text())
    assert [list(b) for b in pool] == [row["block"] for row in saved_pool["pool"]]
    assert len(pool) == 1744
    data = json.loads((HERE / "certificate.json").read_text())
    group, stabilizer, representatives = inspect(data, seeds, pool)
    # Besides generator-level preservation, explicitly test every generated map.
    for mapping in group:
        affine_conditions(mapping)
        assert all({relabel(b, mapping) for b in seed} == seed for seed in seeds)
        assert {relabel(b, mapping) for b in pool} == set(pool)
    mutations = [
        ("wrong-group-order", lambda d: d.__setitem__("group_order", 1535)),
        ("bad-generator", lambda d: d["generators_images_of_1_to_16"][0].__setitem__(0, 0)),
        ("missing-generator", lambda d: d["generators_images_of_1_to_16"].pop()),
        ("wrong-target", lambda d: d.__setitem__("target_triple", [1, 2, 3])),
        ("wrong-stabilizer-order", lambda d: d.__setitem__("stabilizer_order", 47)),
        ("missing-carrier", lambda d: d["carrier_blocks"].pop()),
        ("missing-orbit", lambda d: d["orbits"].pop()),
        ("wrong-orbit-size", lambda d: d["orbits"][0].__setitem__("size", 11)),
        ("duplicate-orbit-member", lambda d: d["orbits"][0]["members"].__setitem__(
            1, d["orbits"][0]["members"][0])),
        ("wrong-carrier-map", lambda d: d["orbits"][0]["members"][1].__setitem__(
            "to_representative", list(IDENTITY))),
        ("wrong-local-id", lambda d: d["representative_local_ids"].__setitem__(0, 0)),
        ("wrong-global-id", lambda d: d["representative_global_ids"].__setitem__(0, 0)),
        ("wrong-pool-hash", lambda d: d.__setitem__("pool_sha256", "0" * 64)),
        ("wrong-model-hash", lambda d: d.__setitem__("base_model_sha256", "0" * 64)),
    ]
    rejected = []
    for name, mutate in mutations:
        broken = copy.deepcopy(data)
        mutate(broken)
        try:
            inspect(broken, seeds, pool)
        except (AssertionError, ValueError, KeyError, IndexError):
            rejected.append(name)
        else:
            raise AssertionError(f"damaged certificate accepted: {name}")
    assert before == {str(p.relative_to(ROOT)): sha(p) for p in checked}
    report = {
        "passed": True, "source_sha256": sha(Path(__file__)), "verified_inputs": before,
        "certificate_sha256": sha(HERE / "certificate.json"),
        "model_sha256": MODEL_HASH, "pool_sha256": POOL_HASH,
        "generator_count": len(data["generators_images_of_1_to_16"]), "group_order": len(group),
        "all_group_maps_explicitly_checked": True, "stabilizer_order": len(stabilizer),
        "carriers": 30, "orbits": 6, "orbit_sizes": [12, 8, 3, 1, 3, 3],
        "representatives": representatives,
        "representative_local_ids": data["representative_local_ids"],
        "representative_global_ids": data["representative_global_ids"],
        "damaged_controls_rejected": rejected, "solver_calls": 0,
        "scope": "For any cover in this fixed pool, one pool automorphism maps a selected "
            "carrier to one of six representatives. This is a complete symmetry selection, "
            "not a requirement that a cover itself be invariant or a global bound.",
    }
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "verified_inputs"}), flush=True)


if __name__ == "__main__":
    main()
