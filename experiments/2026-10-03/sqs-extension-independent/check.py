#!/usr/bin/env python3
# Document:    Independent SQS Extension Construction and Model Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Rebuild the two SQS seeds, scan all five-blocks, and audit the frozen model."""

import copy
import hashlib
import json
import subprocess
import sys
from collections import Counter
from itertools import combinations, product
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

from covering64.core import verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "experiments/2026-10-03/new-construction-web"
RAW = ROOT / "experiments/scratch/new-construction-web-20261003"
POINTS = tuple(range(1, 17))
TRIPLES = list(combinations(POINTS, 3))
ALL_BLOCKS = list(combinations(POINTS, 5))
EXPECTED_MODEL_HASH = "d0a70c16b53c2399ed10eae2deb77b3c817e352a4fc950d7584291b3c249703f"
EXPECTED_POOL_HASH = "b1e0e13ac3787643b25e920d2ce8f83d7119dedcb3c78daaf8316e04510c68c6"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_blocks(path, blocks):
    path.write_text("".join(" ".join(map(str, b)) + "\n" for b in sorted(blocks)))


def read_seed(path):
    return [tuple(map(int, line.split())) for line in path.read_text().splitlines()]


def validate_seed(blocks, expected):
    assert len(blocks) == len(set(blocks)) == 140
    assert blocks == sorted(blocks) == expected
    assert all(len(b) == 4 and len(set(b)) == 4 and set(b) <= set(POINTS) for b in blocks)
    counts = Counter(t for block in blocks for t in combinations(block, 3))
    assert set(counts) == set(TRIPLES) and all(n == 1 for n in counts.values())


def rank2(blocks):
    pivots = {}
    for block in blocks:
        row = sum(1 << (p - 1) for p in block)
        while row:
            lead = row.bit_length() - 1
            if lead in pivots:
                row ^= pivots[lead]
            else:
                pivots[lead] = row
                break
    return len(pivots)


def reconstruct():
    # Each triple determines its unique affine fourth point. This is independent
    # of the source's four-subset filtering implementation.
    affine = set()
    for a, b, c in TRIPLES:
        fourth = ((a - 1) ^ (b - 1) ^ (c - 1)) + 1
        assert fourth not in (a, b, c)
        affine.add(tuple(sorted((a, b, c, fourth))))
    pairs = [(1, 5), (2, 6), (3, 7), (4, 8)]
    transversals = {tuple(sorted(choice)) for choice in product(*pairs)}
    removed = transversals & affine
    inserted = transversals - affine
    assert len(removed) == len(inserted) == 8
    assert Counter(t for b in removed for t in combinations(b, 3)) == Counter(
        t for b in inserted for t in combinations(b, 3))
    traded = affine - removed | inserted
    seeds = [sorted(affine), sorted(traded)]
    pools = []
    for seed in seeds:
        family = set(seed)
        # Scan the complete lexicographic universe instead of extending seeds.
        pools.append([b for b in ALL_BLOCKS if any(q in family for q in combinations(b, 4))])
    union = sorted(set(pools[0]) | set(pools[1]))
    assert len(pools[0]) == len(pools[1]) == 1680 and len(union) == 1744
    assert [rank2(seed) for seed in seeds] == [11, 12]
    return seeds, pools, union, sorted(removed), sorted(inserted)


def inspect_pool(payload, union):
    assert set(payload) == {"pool", "triples", "supports"}
    assert payload["triples"] == [list(t) for t in TRIPLES]
    global_ids = {b: i for i, b in enumerate(ALL_BLOCKS)}
    expected_rows = [{"local_id": i, "global_id": global_ids[b], "block": list(b)}
                     for i, b in enumerate(union)]
    assert payload["pool"] == expected_rows
    supports = [[i for i, b in enumerate(union) if all(p in b for p in t)] for t in TRIPLES]
    assert payload["supports"] == supports
    return supports, [global_ids[b] for b in union]


def inspect_model(proto, supports, global_ids):
    assert {f.name for f, _ in proto.ListFields()} == {"variables", "constraints"}
    assert len(proto.variables) == 1744 and len(proto.constraints) == 561
    for variable, global_id in zip(proto.variables, global_ids, strict=True):
        assert {f.name for f, _ in variable.ListFields()} == {"name", "domain"}
        assert variable.name == f"block_{global_id}" and list(variable.domain) == [0, 1]
    rows = [(list(range(1744)), [64, 64])] + [
        (indices, [1, 2**63 - 1]) for indices in supports]
    for row, (indices, domain) in zip(proto.constraints, rows, strict=True):
        assert {f.name for f, _ in row.ListFields()} == {"linear"}
        assert row.WhichOneof("constraint") == "linear"
        assert {f.name for f, _ in row.linear.ListFields()} == {"vars", "coeffs", "domain"}
        assert list(row.linear.vars) == indices
        assert list(row.linear.coeffs) == [1] * len(indices)
        assert list(row.linear.domain) == domain


def rejected(check, cases):
    labels = []
    for name, value in cases:
        try:
            check(value)
        except (AssertionError, ValueError, IndexError, KeyError, TypeError):
            labels.append(name)
        else:
            raise AssertionError(f"damaged control accepted: {name}")
    return labels


def double_verify(name, blocks, k):
    path = HERE / f"{name}.txt"
    write_blocks(path, blocks)
    package = verify_cover(blocks, 16, k, 3)
    run = subprocess.run(
        [sys.executable, "-I", str(ROOT / "scripts/check_cover.py"), str(path),
         "--k", str(k), "--expected-blocks", str(len(blocks))],
        capture_output=True, text=True, check=False,
    )
    standalone = json.loads(run.stdout)
    assert run.returncode == 0 and package["valid"] and standalone["valid"]
    assert package["canonical_sha256"] == standalone["canonical_sha256"]
    assert standalone["cardinality_matches"] and standalone["uncovered_count"] == 0
    return {"file": path.name, "sha256": digest(path), "package": package,
            "standalone": standalone}


def main():
    manifest = json.loads((SOURCE / "model-manifest.json").read_text())
    checked_paths = [SOURCE / "model-manifest.json", SOURCE / "construction-audit.json",
                     SOURCE / "check_sqs_lift.py", SOURCE / "build_model.py",
                     RAW / "build_model.py", RAW / "union-pool.json",
                     RAW / "exact64-sqs-union.pbtxt", RAW / "sqs16-affine.txt",
                     RAW / "sqs16-traded.txt"]
    before = {str(p.relative_to(ROOT)): digest(p) for p in checked_paths}
    assert digest(RAW / "exact64-sqs-union.pbtxt") == EXPECTED_MODEL_HASH
    assert digest(RAW / "union-pool.json") == EXPECTED_POOL_HASH
    assert manifest["model_sha256"] == EXPECTED_MODEL_HASH
    assert manifest["pool_sha256"] == EXPECTED_POOL_HASH
    assert digest(SOURCE / "build_model.py") == digest(RAW / "build_model.py")
    assert digest(SOURCE / "build_model.py") == manifest["builder_sha256"]
    assert digest(SOURCE / "check_sqs_lift.py") == manifest["construction_checker_sha256"]
    assert digest(SOURCE / "construction-audit.json") == manifest["construction_audit_sha256"]
    seeds, pools, union, removed, inserted = reconstruct()
    for name, expected in zip(("affine", "traded"), seeds, strict=True):
        validate_seed(read_seed(RAW / f"sqs16-{name}.txt"), expected)
    seed_controls = []
    for index, seed in enumerate(seeds):
        seed_controls.extend(rejected(lambda b: validate_seed(b, seed), [
            (f"seed{index}-missing", seed[:-1]),
            (f"seed{index}-duplicate", [seed[0]] + seed[:-1]),
            (f"seed{index}-bad-label", [(0,) + seed[0][1:]] + seed[1:]),
            (f"seed{index}-repeated-label", [(1, 1, 2, 3)] + seed[1:]),
            (f"seed{index}-reordered", [seed[1], seed[0]] + seed[2:]),
        ]))
    payload = json.loads((RAW / "union-pool.json").read_text())
    supports, global_ids = inspect_pool(payload, union)
    assert manifest["global_block_ids_in_variable_order"] == global_ids
    pool_cases = []
    for name, mutate in [
        ("missing-block", lambda p: p["pool"].pop()),
        ("duplicate-block", lambda p: p["pool"].__setitem__(1, p["pool"][0])),
        ("wrong-global-id", lambda p: p["pool"][0].__setitem__("global_id", 100)),
        ("wrong-local-id", lambda p: p["pool"][0].__setitem__("local_id", 100)),
        ("missing-support", lambda p: p["supports"][0].pop()),
        ("extra-support", lambda p: p["supports"][0].append(1743)),
        ("wrong-triple-order", lambda p: p["triples"].reverse()),
    ]:
        changed = copy.deepcopy(payload)
        mutate(changed)
        pool_cases.append((name, changed))
    pool_controls = rejected(lambda p: inspect_pool(p, union), pool_cases)
    proto = cp_model_pb2.CpModelProto()
    text_format.Parse((RAW / "exact64-sqs-union.pbtxt").read_text(), proto)
    inspect_model(proto, supports, global_ids)
    model_cases = []
    for name, mutate in [
        ("missing-variable", lambda p: p.variables.pop()),
        ("nonboolean-domain", lambda p: p.variables[0].domain.__setitem__(1, 2)),
        ("wrong-variable-name", lambda p: setattr(p.variables[0], "name", "wrong")),
        ("cardinality-65", lambda p: p.constraints[0].linear.domain.__setitem__(1, 65)),
        ("missing-row", lambda p: p.constraints.pop()),
        ("extra-row", lambda p: p.constraints.add().CopyFrom(p.constraints[0])),
        ("wrong-cover-bound", lambda p: p.constraints[1].linear.domain.__setitem__(0, 0)),
        ("wrong-cover-variable", lambda p: p.constraints[1].linear.vars.__setitem__(0, 1743)),
        ("wrong-cover-coefficient", lambda p: p.constraints[1].linear.coeffs.__setitem__(0, 2)),
        ("reified-cover", lambda p: p.constraints[1].enforcement_literal.append(0)),
        ("hidden-objective", lambda p: p.objective.vars.append(0)),
        ("hidden-hint", lambda p: p.solution_hint.vars.append(0)),
    ]:
        changed = cp_model_pb2.CpModelProto()
        changed.CopyFrom(proto)
        mutate(changed)
        model_cases.append((name, changed))
    model_controls = rejected(lambda p: inspect_model(p, supports, global_ids), model_cases)
    coverage = [double_verify(name, seed, 4) for name, seed in zip(
        ("affine-independent", "traded-independent"), seeds, strict=True)]
    positive = sorted({tuple(sorted((*q, max(set(POINTS) - set(q))))) for q in seeds[1]})
    assert len(positive) == 140 and set(positive) <= set(union)
    coverage.append(double_verify("extension-positive", positive, 5))
    assert before == {str(p.relative_to(ROOT)): digest(p) for p in checked_paths}
    report = {
        "passed": True, "source_sha256": digest(Path(__file__)),
        "model_sha256": EXPECTED_MODEL_HASH, "pool_sha256": EXPECTED_POOL_HASH,
        "verified_inputs": before, "quadruple_seed_sizes": [140, 140],
        "each_triple_exactly_once": True, "seed_binary_ranks": [11, 12],
        "removed_trade": removed, "inserted_trade": inserted,
        "individual_pool_sizes": list(map(len, pools)), "union_pool_size": len(union),
        "pool_support_histogram": dict(sorted(Counter(map(len, supports)).items())),
        "model_variables": len(proto.variables), "model_rows": len(proto.constraints),
        "coverage_rows": 560, "exact_cardinality": 64, "additional_constraints": False,
        "damaged_seed_controls": seed_controls, "damaged_pool_controls": pool_controls,
        "damaged_model_controls": model_controls, "cover_checks": coverage,
        "solver_calls": 0,
        "scope": "Exact64 feasibility in the union of two specified SQS extension pools. "
                 "Gate certifies this encoding, not completeness for unrestricted coverings.",
    }
    (HERE / "gate.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in (
        "cover_checks", "verified_inputs", "removed_trade", "inserted_trade")}), flush=True)


if __name__ == "__main__":
    main()
