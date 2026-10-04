# Document:    Steiner Quadruple System Extension Pool Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      bb5d244986c8b5313b7c5835247432cadf28827451efaa3082a24fd1e4ea45dd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Construct two nonisomorphic SQS16 seeds and audit their five-block lifts."""

import hashlib
import itertools
import json
import operator
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from functools import reduce
from pathlib import Path

from covering64.core import verify_cover, write_blocks

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/new-construction-web-20261003"
POINTS = tuple(range(1, 17))
TRIPLES = tuple(itertools.combinations(POINTS, 3))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_sqs(blocks):
    assert len(blocks) == len(set(blocks)) == 140
    assert all(len(b) == 4 and tuple(sorted(set(b))) == b and set(b) <= set(POINTS) for b in blocks)
    counts = Counter(t for b in blocks for t in itertools.combinations(b, 3))
    assert set(counts) == set(TRIPLES) and set(counts.values()) == {1}


def binary_rank(blocks):
    basis = {}
    for block in blocks:
        mask = sum(1 << (point - 1) for point in block)
        while mask:
            pivot = mask.bit_length() - 1
            if pivot in basis:
                mask ^= basis[pivot]
            else:
                basis[pivot] = mask
                break
    return len(basis)


def extension_pool(seeds):
    return sorted(
        {
            tuple(sorted((*block, point)))
            for blocks in seeds
            for block in blocks
            for point in POINTS
            if point not in block
        }
    )


def validate_pool(pool, seeds):
    assert len(pool) == len(set(pool))
    assert pool == extension_pool(seeds)
    assert all(len(b) == 5 and tuple(sorted(set(b))) == b and set(b) <= set(POINTS) for b in pool)


def double_verify(name, blocks, k):
    path = RAW / f"{name}.txt"
    write_blocks(path, blocks)
    package = verify_cover(blocks, 16, k, 3)
    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_cover.py",
            str(path),
            "--v",
            "16",
            "--k",
            str(k),
            "--t",
            "3",
            "--expected-blocks",
            str(len(blocks)),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    standalone = json.loads(result.stdout)
    assert package["valid"] and standalone["valid"]
    assert package["canonical_sha256"] == standalone["canonical_sha256"]
    assert package["blocks"] == standalone["blocks"] == len(blocks)
    (RAW / f"{name}-package.json").write_text(json.dumps(package, indent=2) + "\n")
    (RAW / f"{name}-standalone.json").write_text(json.dumps(standalone, indent=2) + "\n")
    return {
        "file": str(path.relative_to(ROOT)),
        "sha256": digest(path),
        "blocks": len(blocks),
        "k": k,
        "both_verifiers_passed": True,
    }


def main():
    assert not (HERE / "construction-audit.json").exists(), "preserve completed finite audit"
    affine = sorted(
        b
        for b in itertools.combinations(POINTS, 4)
        if reduce(operator.xor, (p - 1 for p in b)) == 0
    )
    positive, negative = [], []
    for bits in itertools.product(range(2), repeat=4):
        block = tuple(sorted(i + 4 * bit + 1 for i, bit in enumerate(bits)))
        (positive if sum(bits) % 2 == 0 else negative).append(block)
    assert len(positive) == len(negative) == 8
    assert set(positive) <= set(affine) and not set(negative) & set(affine)
    assert Counter(t for b in positive for t in itertools.combinations(b, 3)) == Counter(
        t for b in negative for t in itertools.combinations(b, 3)
    )
    traded = sorted(set(affine) - set(positive) | set(negative))
    for seed in (affine, traded):
        validate_sqs(seed)
    assert binary_rank(affine) == 11 and binary_rank(traded) == 12
    verified = [double_verify("sqs16-affine", affine, 4), double_verify("sqs16-traded", traded, 4)]
    controls = [
        affine[:-1],
        affine + [affine[0]],
        [affine[0]] + affine[:-1],
        [(0,) + affine[0][1:]] + affine[1:],
        [(affine[0][0],) * 4] + affine[1:],
    ]
    for broken in controls:
        try:
            validate_sqs(broken)
        except AssertionError:
            continue
        raise AssertionError("damaged SQS accepted")
    universe = list(itertools.combinations(POINTS, 5))
    global_ids = {b: i for i, b in enumerate(universe)}
    previous_file = ROOT / "experiments/scratch/affine-cap-extension-pool-20261003/pool.json"
    previous = {tuple(row["block"]) for row in json.loads(previous_file.read_text())["pool"]}
    assert len(previous) == 528
    results = []
    for name, seeds in [("affine", [affine]), ("traded", [traded]), ("union", [affine, traded])]:
        pool = extension_pool(seeds)
        validate_pool(pool, seeds)
        assert len(pool) == (1744 if name == "union" else 1680)
        supports = [
            [i for i, block in enumerate(pool) if set(triple) <= set(block)] for triple in TRIPLES
        ]
        histogram = Counter(map(len, supports))
        if name != "union":
            assert histogram == {30: 560}
        for broken in (pool[:-1], [pool[0]] + pool[:-1], pool + [pool[0]]):
            try:
                validate_pool(broken, seeds)
            except AssertionError:
                continue
            raise AssertionError("damaged pool accepted")
        payload = {
            "pool": [
                {"local_id": i, "global_id": global_ids[b], "block": b} for i, b in enumerate(pool)
            ],
            "triples": TRIPLES,
            "supports": supports,
        }
        path = RAW / f"{name}-pool.json"
        path.write_text(json.dumps(payload, indent=2) + "\n")
        positive_control = sorted(
            {tuple(sorted((*b, next(p for p in POINTS if p not in b)))) for b in seeds[0]}
        )
        assert len(positive_control) == 140 and set(positive_control) <= set(pool)
        verified.append(double_verify(f"{name}-extension-positive-control", positive_control, 5))
        results.append(
            {
                "name": name,
                "blocks": len(pool),
                "sha256": digest(path),
                "support_histogram": dict(sorted(histogram.items())),
                "intersection_with_previous528": len(set(pool) & previous),
                "new_blocks_outside_previous528": len(set(pool) - previous),
            }
        )
    report = {
        "passed": True,
        "utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": digest(Path(__file__)),
        "paper_sha256": digest(RAW / "sqs16.pdf"),
        "previous528_pool_sha256": digest(previous_file),
        "seed_binary_ranks": [11, 12],
        "positive_trade": positive,
        "negative_trade": negative,
        "pools": results,
        "double_verified_seeds_and_controls": verified,
        "damaged_seed_controls": len(controls),
        "damaged_pool_controls": 9,
        "solver_calls": 0,
        "cover64_found": False,
        "scope": "Two explicitly constructed SQS16 seeds and their lifted pools; "
        "no theorem concerning all64-block covers or allSQS16 designs.",
    }
    (HERE / "construction-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in ("positive_trade", "negative_trade")}
        )
    )


if __name__ == "__main__":
    main()
