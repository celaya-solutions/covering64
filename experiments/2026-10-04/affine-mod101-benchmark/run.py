# Document:    Stratified Prime-101 Residual Equation Benchmark
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      7983772d2e89b10f74d02072facdc393709ec7d7c40d1c286ce3faa84dbd71c2
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""A frozen 32-case linear-algebra benchmark; no optimizer or full-pool screen."""

import gzip
import json
import struct
import subprocess
import sys
import time
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import combinations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
PARITY = BASE / "affine-mod2-pilot"
OLD = BASE / "circulant-chosen-link-catalog"
EXPANDED = BASE / "affine-expanded-catalog"
PRIME = 101
SECONDS = 15.0
BLOCKS = tuple(combinations(range(1, 17), 5))
TRIPLES = tuple(combinations(range(2, 17), 3))
RANK = {triple: i for i, triple in enumerate(TRIPLES)}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def prepare():
    require(not (HERE / "manifest.json").exists(), "fresh source and plan freeze")
    require(
        sha(PARITY / "result.json")
        == "aacc0a5cd51bc8315e8b72dd1f14d7376b4241237672fbbceceec6d7e3288c71",
        "exact parity result pin",
    )
    receipt = load(PARITY / "result.json")
    require(receipt["complete"] and len(receipt["results"]) == 1121, "complete parity source")
    require(sha(PARITY / "executed-source.txt") == receipt["source_sha256"], "executed source")
    require(sha(PARITY / "manifest.json") == receipt["manifest_sha256"], "executed manifest")
    old_partials = load(OLD / "partial-catalog.json")
    old_fibers = load(OLD / "link-fibers.json")
    expanded_fibers = load(EXPANDED / "link-fibers.json")
    groups = defaultdict(list)
    expanded = []
    pool = []
    for index, row in enumerate(receipt["results"]):
        if row["outcome"] != "parity_consistent":
            continue
        kind = (
            old_fibers[old_partials[row["partial_id"]]["excess_link_id"]]["class"]
            if row["catalog"] == "original"
            else expanded_fibers[row["partial_id"] // 5184]["class"]
        )
        item = {
            "parity_result_index": index,
            "catalog": row["catalog"],
            "class": kind,
            "pair_ordinal": row["pair_ordinal"],
            "partial_id": row["partial_id"],
            "profile_id": row["profile_id"],
            "zero_demand_domain_size": row["eligible_count"],
            "GF2_rank": row["rank"],
            "GF2_nullity": row["eligible_count"] - row["rank"],
        }
        pool.append(item)
        if row["catalog"] == "expanded_sample":
            expanded.append(item)
        else:
            groups[kind].append(item)
    require(len(pool) == 616 and len(expanded) == 4, "616-case pool and four expanded cases")
    require(
        {k: len(v) for k, v in groups.items()}
        == {"C4-leaf": 226, "triangle-path2": 380, "triangle-two-leaves": 6},
        "old strata",
    )

    def key(row):
        return row["zero_demand_domain_size"], row["GF2_nullity"], row["pair_ordinal"]

    selected = {}
    for kind, rows in sorted(groups.items()):
        ordered = sorted(rows, key=key)
        count = 6 if kind == "triangle-two-leaves" else 11
        positions = [i * (len(ordered) - 1) // (count - 1) for i in range(count)]
        selected[kind] = [ordered[i] | {"within_core_sorted_index": i} for i in positions]
    plan = sorted(expanded, key=lambda row: (row["class"], *key(row)))
    for i in range(11):
        for kind in sorted(selected):
            if i < len(selected[kind]):
                plan.append(selected[kind][i])
    plan = [row | {"benchmark_index": i} for i, row in enumerate(plan)]
    require(len(plan) == len({r["parity_result_index"] for r in plan}) == 32, "unique32 plan")
    dump("plan.json", plan)
    summary = load(EXPANDED / "summary.json")
    inputs = {
        PARITY / "result.json",
        PARITY / "manifest.json",
        PARITY / "executed-source.txt",
        OLD / "partial-catalog.json",
        OLD / "profiles.json",
        OLD / "link-fibers.json",
        EXPANDED / "summary.json",
        EXPANDED / "link-fibers.json",
        ROOT / summary["catalog_path"],
        HERE / "plan.json",
    }
    dump(
        "manifest.json",
        {
            "source_sha256": sha(__file__),
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "input_hashes": {str(p.relative_to(ROOT)): sha(p) for p in sorted(inputs)},
            "prime": PRIME,
            "cooperative_seconds": SECONDS,
            "planned_cases": 32,
            "pool_cases": 616,
            "expanded_cases": 4,
            "old_cases": 28,
            "old_selection": "all six rare-core cases plus 11 domain-size quantiles per large core",
            "free_size_definition": (
                "candidate count after zero-demand removal, before any forced cuts"
            ),
            "selection_tie_breakers": ["GF2_nullity", "pair_ordinal"],
            "source_domain": "all3003 original avoiding-point blocks; only zero-demand removals",
            "equations": "all455 residual triple rows and the sum44 row",
            "arithmetic": (
                "NumPy int64 Gaussian elimination modulo101 with tracked456-row combinations"
            ),
            "certificate_contradiction": "dense y with yA=0 and yb nonzero modulo101",
            "certificate_consistent": (
                "dense field solution x with Ax=b modulo101; not a binary cover"
            ),
            "finalize_reserve_seconds": 0.15,
            "time_scope": "input validation, loading, matrix building, elimination, output",
            "full616_screen_authorized": False,
            "optimizer_calls": 0,
        },
    )
    print(
        json.dumps(
            {
                "source_sha256": sha(__file__),
                "manifest_sha256": sha(HERE / "manifest.json"),
                "plan_sha256": sha(HERE / "plan.json"),
                "cases": 32,
            },
            sort_keys=True,
        )
    )


def eliminate(matrix, rhs, deadline):
    """Echelon form of [A|b|I]; every operation is reduced before the next."""
    rows, columns = matrix.shape
    work = np.concatenate((matrix, rhs[:, None], np.eye(rows, dtype=np.int64)), axis=1)
    pivots = []
    for column in range(columns):
        if time.monotonic() >= deadline:
            return {
                "outcome": "inconclusive_timeout",
                "rank_so_far": len(pivots),
                "rank_is_complete": False,
                "certificate": None,
            }
        rank = len(pivots)
        candidates = np.flatnonzero(work[rank:, column])
        if candidates.size == 0:
            continue
        pivot = rank + int(candidates[0])
        if pivot != rank:
            work[[rank, pivot]] = work[[pivot, rank]]
        inverse = pow(int(work[rank, column]), -1, PRIME)
        work[rank, column:] = (work[rank, column:] * inverse) % PRIME
        affected = np.flatnonzero(work[rank + 1 :, column]) + rank + 1
        if affected.size:
            factors = work[affected, column].copy()
            work[affected, column + 1 :] = (
                work[affected, column + 1 :] - factors[:, None] * work[rank, column + 1 :]
            ) % PRIME
            work[affected, column] = 0
        pivots.append(column)
        if len(pivots) == rows:
            break
    rank = len(pivots)
    require(not np.any(work[rank:, :columns]), "complete row-echelon zero remainder")
    impossible = np.flatnonzero(work[rank:, columns])
    base = {"rank": rank, "rank_is_complete": True, "pivot_columns": pivots}
    if impossible.size:
        row = rank + int(impossible[0])
        weights = work[row, columns + 1 :].copy()
        residue = int(weights @ rhs % PRIME)
        require(not np.any(weights @ matrix % PRIME) and residue != 0, "direct contradiction")
        require(residue == int(work[row, columns]), "tracked right-hand side")
        return base | {
            "outcome": "mod101_contradiction",
            "augmented_rank": rank + 1,
            "certificate": {
                "kind": "left_nullspace_contradiction",
                "row_coefficients": weights.tolist(),
                "rhs_residue": residue,
            },
        }
    solution = np.zeros(columns, dtype=np.int64)
    for row in reversed(range(rank)):
        column = pivots[row]
        solution[column] = (
            int(work[row, columns]) - int(work[row, column + 1 : columns] @ solution[column + 1 :])
        ) % PRIME
    require(np.array_equal(matrix @ solution % PRIME, rhs % PRIME), "direct field solution")
    return base | {
        "outcome": "mod101_consistent",
        "augmented_rank": rank,
        "certificate": {"kind": "field_solution", "values": solution.tolist()},
    }


def benchmark():
    started = time.monotonic()
    require(not (HERE / "result.json").exists(), "no replay or retry of frozen benchmark")
    manifest = load(HERE / "manifest.json")
    require(sha(__file__) == manifest["source_sha256"], "source freeze")
    for relative, expected in manifest["input_hashes"].items():
        require(sha(ROOT / relative) == expected, "input freeze")
    plan = load(HERE / "plan.json")
    partials = load(OLD / "partial-catalog.json")
    summary = load(EXPANDED / "summary.json")
    packed = gzip.decompress((ROOT / summary["catalog_path"]).read_bytes())
    profiles = [
        {RANK[tuple(t)] for t in row["excess_triples"] if 1 not in t}
        for row in load(OLD / "profiles.json")
    ]
    carrier = np.zeros((456, 3003), dtype=np.int64)
    for column, block in enumerate(BLOCKS[1365:]):
        for triple in combinations(block, 3):
            carrier[RANK[triple], column] = 1
    carrier[455, :] = 1
    require(np.all(carrier[:455].sum(axis=1) == 66), "complete carrier domain")
    results = []
    for case in plan:
        if time.monotonic() - started >= SECONDS - 0.15:
            break
        case_started = time.monotonic()
        ids = (
            partials[case["partial_id"]]["global_block_ids"]
            if case["catalog"] == "original"
            else struct.unpack_from("<20H", packed, 40 * case["partial_id"])
        )
        require(len(set(ids)) == 20 and max(ids) < 1365, "original point-one partial")
        fixed = [RANK[t] for i in ids for t in combinations(BLOCKS[i][1:], 3)]
        require(len(fixed) == len(set(fixed)) == 80, "eighty partial outside triples")
        rhs = np.ones(456, dtype=np.int64)
        rhs[list(profiles[case["profile_id"]])] += 1
        rhs[fixed] -= 1
        rhs[455] = 44
        require(np.all(rhs >= 0) and int(rhs[:455].sum()) == 440, "original residual demands")
        zero_rows = np.flatnonzero(rhs[:455] == 0)
        eligible = np.flatnonzero(~np.any(carrier[zero_rows, :] != 0, axis=0))
        require(len(eligible) == case["zero_demand_domain_size"], "original zero-only domain")
        matrix = carrier[:, eligible].copy()
        result = eliminate(matrix, rhs, started + SECONDS - 0.15)
        result.update(case)
        result.update(
            {
                "eligible_global_block_ids": (eligible + 1365).tolist(),
                "zero_demand_rows": zero_rows.tolist(),
                "elapsed_seconds": time.monotonic() - case_started,
            }
        )
        results.append(result)
        if result["outcome"] == "inconclusive_timeout":
            break
    receipt = {
        "complete": len(results) == len(plan)
        and all(r["outcome"] != "inconclusive_timeout" for r in results),
        "planned_cases": len(plan),
        "processed_cases": len(results),
        "results": results,
        "outcomes": dict(Counter(r["outcome"] for r in results)),
        "elapsed_before_receipt_seconds": time.monotonic() - started,
        "cooperative_seconds": SECONDS,
        "next_benchmark_index": len(results),
        "timeout_case_requires_fresh_explicit_request": any(
            r["outcome"] == "inconclusive_timeout" for r in results
        ),
        "source_sha256": sha(__file__),
        "manifest_sha256": sha(HERE / "manifest.json"),
        "numpy_version": np.__version__,
        "python_version": sys.version,
        "optimizer_calls": 0,
        "full616_screen_started": False,
    }
    dump("result.json", receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != "results"}, sort_keys=True))


if __name__ == "__main__":
    require(len(sys.argv) == 2 and sys.argv[1] in ("prepare", "benchmark"), "explicit mode")
    (prepare if sys.argv[1] == "prepare" else benchmark)()
