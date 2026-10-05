# Document:    Residual Parity Certificate Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      bf7bd9b805e7e0cf0d26f22a96f09ec89e1b7679b6724af024a09fef6b040c88
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Finite GF(2) row elimination; no optimizer, only zero-demand column removal."""

import gzip
import hashlib
import json
import struct
import time
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
TRIPLES = tuple(combinations(range(2, 17), 3))
BLOCKS = tuple(combinations(range(1, 17), 5))
RANK = {t: i for i, t in enumerate(TRIPLES)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def parity(rows, rhs):
    pivots = {}
    for row_id, (coefficients, value) in enumerate(zip(rows, rhs, strict=True)):
        combination = 1 << row_id
        value %= 2
        while coefficients:
            pivot = (coefficients & -coefficients).bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = coefficients, value, combination
                break
            stored, stored_value, stored_combination = pivots[pivot]
            coefficients ^= stored
            value ^= stored_value
            combination ^= stored_combination
        if not coefficients and value:
            return {
                "outcome": "parity_contradiction",
                "rank_before_contradiction": len(pivots),
                "xor_rows": [i for i in range(456) if (combination >> i) & 1],
            }
    return {"outcome": "parity_consistent", "rank": len(pivots)}


def main():
    started = time.monotonic()
    assert not (HERE / "result.json").exists()
    old = BASE / "circulant-chosen-link-catalog"
    expanded = BASE / "affine-expanded-catalog"
    originals = (
        ROOT
        / "experiments/scratch/circulant-chosen-link-row-propagation-full-v1.0.0/survivors.jsonl.gz"
    )
    samples = ROOT / "experiments/scratch/affine-expanded-benchmark-v1.0.0/survivors.jsonl.gz"
    summary = load(expanded / "summary.json")
    catalog = ROOT / summary["catalog_path"]
    inputs = [
        old / "partial-catalog.json",
        old / "profiles.json",
        originals,
        samples,
        expanded / "summary.json",
        catalog,
    ]
    manifest = {
        "source_sha256": sha(Path(__file__)),
        "inputs": {str(p.relative_to(ROOT)): sha(p) for p in inputs},
        "cooperative_seconds": 10,
        "planned_cases": 1121,
        "scope": (
            "1096 original row-fixed-points and25 expanded sample survivors; "
            "only zero-demand pruning"
        ),
        "optimizer_calls": 0,
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    old_partials = load(old / "partial-catalog.json")
    families = list(struct.iter_unpack("<20H", gzip.decompress(catalog.read_bytes())))
    profiles = [
        {RANK[tuple(t)] for t in row["excess_triples"] if 1 not in t}
        for row in load(old / "profiles.json")
    ]
    carriers = [0] * 455
    for i, block in enumerate(BLOCKS[1365:]):
        for triple in combinations(block, 3):
            carriers[RANK[triple]] |= 1 << i
    cases = []
    for stream, kind in ((originals, "original"), (samples, "expanded_sample")):
        for line in gzip.open(stream, "rt"):
            record = json.loads(line)
            cases.append(
                {k: record[k] for k in ("pair_ordinal", "partial_id", "profile_id")}
                | {"catalog": kind}
            )
    assert len(cases) == 1121
    results = []
    for case in cases:
        if time.monotonic() - started > 10:
            break
        ids = (
            old_partials[case["partial_id"]]["global_block_ids"]
            if case["catalog"] == "original"
            else families[case["partial_id"]]
        )
        fixed = {RANK[t] for i in ids for t in combinations(BLOCKS[i][1:], 3)}
        excess = profiles[case["profile_id"]]
        demand = [1 + int(i in excess) - int(i in fixed) for i in range(455)]
        eligible = (1 << 3003) - 1
        for i, value in enumerate(demand):
            if value == 0:
                eligible &= ~carriers[i]
        rows = [row & eligible for row in carriers] + [eligible]
        result = parity(rows, [*demand, 44])
        if result["outcome"] == "parity_contradiction":
            check_coefficients, check_value = 0, 0
            for i in result["xor_rows"]:
                check_coefficients ^= rows[i]
                check_value ^= [*demand, 44][i] % 2
            assert check_coefficients == 0 and check_value == 1
        results.append(case | result | {"eligible_count": eligible.bit_count()})
    receipt = {
        "complete": len(results) == len(cases),
        "elapsed_seconds": time.monotonic() - started,
        "source_sha256": sha(Path(__file__)),
        "manifest_sha256": sha(HERE / "manifest.json"),
        "results": results,
        "optimizer_calls": 0,
    }
    (HERE / "result.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    from collections import Counter

    print(
        json.dumps(
            {
                "complete": receipt["complete"],
                "elapsed_seconds": receipt["elapsed_seconds"],
                "outcomes": dict(Counter(r["outcome"] for r in results)),
                "result_sha256": sha(HERE / "result.json"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
