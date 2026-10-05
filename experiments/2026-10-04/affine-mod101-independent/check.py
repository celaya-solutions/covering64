# Document:    Independent Prime-101 Certificate Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      51cef78c076eecb8b8e4c78ac2a158ceda7de4291fb6babc362839cf0d6bb61c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay the 32 saved prime-101 outcomes without the producer's code or NumPy.

Each case is rebuilt from the frozen catalogs: twenty fixed point-one blocks,
the eighty excess triples of its profile, exact residual demands on the 455
triples avoiding point one, and the sum-44 row. Columns meeting a zero-demand
triple are dropped. A contradiction needs yA = 0 on every kept column and
yb != 0 modulo 101. A consistent case needs Ax = b modulo 101.
"""

import copy
import gzip
import json
import struct
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

P = 101
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
PRODUCER = BASE / "affine-mod101-benchmark"
PARITY = BASE / "affine-mod2-pilot"
OLD = BASE / "circulant-chosen-link-catalog"
EXPANDED = BASE / "affine-expanded-catalog"
PINS = {
    PRODUCER / "result.json": "5b8997b6c50775fdb0d1e3a852b87b5d1b4ca4ee7d1ef690c8b3c586ba457154",
    PRODUCER / "manifest.json": "3ab0c3d2a37664fea42c099aa47ee3f5c3052fea15b4b120c3422b3e03f1d119",
    PRODUCER / "plan.json": "3dbc3eafd965fa8f2a6d7c92f98c50350d07a1a3521e5c598de7d84f82aff3ac",
    PRODUCER / "run.py": "040cefb73c53c93381a0928b98cdd5ad900799590e12dcec0184bd9e1871db72",
    PARITY / "result.json": "aacc0a5cd51bc8315e8b72dd1f14d7376b4241237672fbbceceec6d7e3288c71",
}
BLOCKS = tuple(combinations(range(1, 17), 5))
OUTSIDE = BLOCKS[1365:]
TRIPLES = tuple(combinations(range(2, 17), 3))
TRIPLE_ROW = {triple: row for row, triple in enumerate(TRIPLES)}
SUM_ROW = 455


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def block_rows(global_id):
    """Rows met by one point-one-free block: its ten triples and the sum row."""
    block = BLOCKS[global_id]
    require(1 not in block, "completion block avoids point one")
    return [TRIPLE_ROW[t] for t in combinations(block, 3)] + [SUM_ROW]


def system(ids, profile):
    """Exact residual demands and the zero-demand-safe column list."""
    require(len(ids) == 20 and list(ids) == sorted(set(ids)), "twenty sorted partial blocks")
    require(all(0 <= i < 1365 and 1 in BLOCKS[i] for i in ids), "partial blocks contain point 1")
    counts = Counter(t for i in ids for t in combinations(BLOCKS[i], 3))
    excess = {tuple(t) for t in profile["excess_triples"]}
    require(len(excess) == 80, "eighty excess triples")
    for a, b in combinations(range(2, 17), 2):
        require(counts[(1, a, b)] == 1 + ((1, a, b) in excess), "point-one rows met exactly")
    demand = [1 + (t in excess) - counts[t] for t in TRIPLES]
    require(min(demand) >= 0 and sum(demand) == 440, "nonnegative demands summing to 440")
    zero = {row for row, d in enumerate(demand) if d == 0}
    kept = [
        1365 + j
        for j, block in enumerate(OUTSIDE)
        if not any(TRIPLE_ROW[t] in zero for t in combinations(block, 3))
    ]
    return demand + [44], sorted(zero), kept


def check_contradiction(y, rhs, kept, residue):
    require(len(y) == 456 and all(type(v) is int and 0 <= v < P for v in y), "dense y in Z_101")
    for column in kept:
        require(sum(y[row] for row in block_rows(column)) % P == 0, "yA vanishes on a column")
    value = sum(a * b for a, b in zip(y, rhs, strict=True)) % P
    require(value != 0 and value == residue, "nonzero saved residue")


def check_solution(x, rhs, kept):
    require(len(x) == len(kept) and all(type(v) is int and 0 <= v < P for v in x), "dense x")
    total = [0] * 456
    for column, value in zip(kept, x, strict=True):
        for row in block_rows(column):
            total[row] += value
    require(all((t - b) % P == 0 for t, b in zip(total, rhs, strict=True)), "Ax = b mod 101")


def reject(label, operation):
    try:
        operation()
    except AssertionError:
        return label
    raise AssertionError(f"damaged control accepted: {label}")


def main():
    for path, expected in PINS.items():
        require(digest(path) == expected, f"pinned input {path.name}")
    manifest = read(PRODUCER / "manifest.json")
    for path, expected in manifest["input_hashes"].items():
        require(digest(ROOT / path) == expected, f"manifest input {path}")
    result = read(PRODUCER / "result.json")
    require(result["complete"] is True and result["processed_cases"] == 32, "complete run")
    require(result["optimizer_calls"] == 0, "no optimizer")
    parity = read(PARITY / "result.json")["results"]
    pool = {
        (r["catalog"], r["pair_ordinal"], r["partial_id"], r["profile_id"])
        for r in parity
        if r["outcome"] == "parity_consistent"
    }
    require(len(pool) == 616, "616 parity-consistent cases")
    old_partials = read(OLD / "partial-catalog.json")
    profiles = read(OLD / "profiles.json")
    summary = read(EXPANDED / "summary.json")
    packed = gzip.decompress((ROOT / summary["catalog_path"]).read_bytes())
    require(sha256(packed).hexdigest() == summary["catalog_uncompressed_sha256"], "packed catalog")
    outcomes, cases, bad, good = Counter(), [], None, None
    for record in result["results"]:
        key = (
            record["catalog"],
            record["pair_ordinal"],
            record["partial_id"],
            record["profile_id"],
        )
        require(key in pool, "case drawn from the parity-consistent pool")
        if record["catalog"] == "expanded_sample":
            ids = list(struct.unpack_from("<20H", packed, record["partial_id"] * 40))
        else:
            require(record["catalog"] == "original", "known catalog")
            entry = old_partials[record["partial_id"]]
            require(entry["partial_id"] == record["partial_id"], "original partial index")
            ids = entry["global_block_ids"]
        rhs, zero, kept = system(ids, profiles[record["profile_id"]])
        require(record["zero_demand_rows"] == zero, "zero-demand rows")
        require(record["eligible_global_block_ids"] == kept, "eligible columns")
        require(record["zero_demand_domain_size"] == len(kept), "eligible count")
        certificate = record["certificate"]
        if record["outcome"] == "mod101_contradiction":
            require(certificate["kind"] == "left_nullspace_contradiction", "contradiction kind")
            check_contradiction(
                certificate["row_coefficients"], rhs, kept, certificate["rhs_residue"]
            )
            bad = bad or (record, rhs, kept)
        else:
            require(record["outcome"] == "mod101_consistent", "known outcome")
            require(certificate["kind"] == "field_solution", "solution kind")
            check_solution(certificate["values"], rhs, kept)
            good = good or (record, rhs, kept)
        outcomes[record["outcome"]] += 1
        cases.append(
            {
                "catalog": record["catalog"],
                "class": record["class"],
                "eligible": len(kept),
                "outcome": record["outcome"],
                "pair_ordinal": record["pair_ordinal"],
            }
        )
    require(outcomes == Counter(result["outcomes"]), "outcome totals")

    controls = []
    record, rhs, kept = bad
    y = list(record["certificate"]["row_coefficients"])
    residue = record["certificate"]["rhs_residue"]
    flipped = copy.copy(y)
    index = next(i for i, v in enumerate(flipped) if v)
    flipped[index] = (flipped[index] + 1) % P
    controls.append(
        reject(
            "one row coefficient changed", lambda: check_contradiction(flipped, rhs, kept, residue)
        )
    )
    controls.append(
        reject("zero certificate", lambda: check_contradiction([0] * 456, rhs, kept, 0))
    )
    controls.append(
        reject("wrong saved residue", lambda: check_contradiction(y, rhs, kept, (residue + 1) % P))
    )
    used = next(i for i, v in enumerate(y) if v)
    shifted = [d + (i == used) for i, d in enumerate(rhs)]
    controls.append(
        reject("used demand changed", lambda: check_contradiction(y, shifted, kept, residue))
    )
    outside = next(
        j for j in range(1365, 4368) if j not in kept and sum(y[r] for r in block_rows(j)) % P
    )
    controls.append(
        reject(
            "dropped column restored",
            lambda: check_contradiction(y, rhs, sorted([*kept, outside]), residue),
        )
    )
    record, rhs, kept = good
    x = list(record["certificate"]["values"])
    changed = copy.copy(x)
    changed[0] = (changed[0] + 1) % P
    controls.append(
        reject("one solution value changed", lambda: check_solution(changed, rhs, kept))
    )
    controls.append(reject("solution truncated", lambda: check_solution(x[:-1], rhs, kept)))
    controls.append(reject("negative value", lambda: check_solution([-1] + x[1:], rhs, kept)))

    review = {
        "cases": cases,
        "checker_sha256": digest(Path(__file__)),
        "damaged_controls_rejected": controls,
        "independent_of": "producer source and NumPy; plain integer arithmetic",
        "input_pins": {str(p.relative_to(ROOT)): h for p, h in PINS.items()},
        "optimizer_calls": 0,
        "outcomes": dict(sorted(outcomes.items())),
        "passed": True,
        "scope": (
            "32 fixed partial/profile systems only. A contradiction excludes that one "
            "conditional completion; a field solution is a necessary condition, not a cover."
        ),
    }
    (HERE / "review.json").write_text(json.dumps(review, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: review[k] for k in ("outcomes", "passed")}), len(controls), "controls")


if __name__ == "__main__":
    main()
