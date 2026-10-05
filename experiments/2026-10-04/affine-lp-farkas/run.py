# Document:    Bounded LP Farkas Screen for Affine Link Completions
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      b09e62c3de1395ccecc5c9dab0de44287fe5b56e3a76ed88af6b9284fe6c0062
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Exclude fixed point-one link/profile completions with exact LP certificates.

Each case fixes twenty point-one blocks and one excess profile. The 44 remaining
blocks avoid point one and must meet every residual triple exactly
d_t = 1 + e_t - l_t times. Columns meeting a zero-demand triple are dropped.
For the remaining 0/1 matrix A (positive-demand rows plus the sum-44 row), any
integer vector Y with  b.Y - sum_j max(0, (A^T Y)_j) > 0  proves that no x in
[0,1]^n solves Ax = b, because b.Y = sum_j x_j (A^T Y)_j <= sum_j max(0, (A^T Y)_j).
GLOP proposes Y; exact integer arithmetic accepts or rejects it. Cases without
an accepted certificate are reported, never silently excluded.
"""

import argparse
import gzip
import json
import platform
import struct
import sys
import time
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
from math import lcm
from multiprocessing import get_context
from pathlib import Path

from ortools import __version__ as ORTOOLS_VERSION
from ortools.linear_solver import pywraplp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
OLD = BASE / "circulant-chosen-link-catalog"
EXPANDED = BASE / "affine-expanded-catalog"
SCRATCH = ROOT / "experiments/scratch"
STREAMS = {
    "original": (
        SCRATCH / "circulant-chosen-link-row-propagation-full-v1.0.0/survivors.jsonl.gz",
        "60e42a6855fc897130c80d8db8189cd9639e0981555386e5938ed02a5eda90ed",
        1096,
    ),
    "expanded": (
        SCRATCH / "affine-expanded-full-support-v1.0.0/survivors.jsonl.gz",
        "340a1bbf418a1a72a1cb4dced4a27b25e43b38add9614180a7d31bcb4af7ec04",
        207474,
    ),
}
PINS = {
    OLD
    / "partial-catalog.json": "cc799f7d289120ff4ebdf101e4f896bb512179a2424883a1e374ea7ace534667",
    OLD / "profiles.json": "24ccef8eb95cd04e683a575d60fcba854728615ee2ca6495f2bc6028fc56cf0f",
    EXPANDED / "summary.json": "e85200dbdf2a392d192973904bc638e4e55184cdc70e1f8cbe3c7643c19ecd6a",
}
BLOCKS = tuple(combinations(range(1, 17), 5))
TRIPLES = tuple(combinations(range(2, 17), 3))
TRIPLE_ROW = {triple: row for row, triple in enumerate(TRIPLES)}
SUM_ROW = 455
COLUMN_ROWS = {
    j: tuple(TRIPLE_ROW[t] for t in combinations(BLOCKS[j], 3)) for j in range(1365, 4368)
}
DENOMINATORS = (12, 60, 840, 27720, 720720, 10**9)
CONTEXT = {}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def load_context():
    for path, expected in PINS.items():
        require(digest(path) == expected, f"pinned input {path.name}")
    summary = json.loads((EXPANDED / "summary.json").read_text())
    packed = gzip.decompress((ROOT / summary["catalog_path"]).read_bytes())
    require(sha256(packed).hexdigest() == summary["catalog_uncompressed_sha256"], "packed catalog")
    partials = json.loads((OLD / "partial-catalog.json").read_text())
    profiles = json.loads((OLD / "profiles.json").read_text())
    return {
        "original": [p["global_block_ids"] for p in partials],
        "packed": packed,
        "excess": [frozenset(map(tuple, p["excess_triples"])) for p in profiles],
    }


def partial_ids(context, catalog, partial_id):
    if catalog == "original":
        return list(context["original"][partial_id])
    return list(struct.unpack_from("<20H", context["packed"], partial_id * 40))


def build_system(ids, excess):
    """Residual demands, kept columns and positive rows for one fixed case."""
    require(len(ids) == 20 and len(set(ids)) == 20, "twenty distinct partial blocks")
    require(all(0 <= i < 1365 for i in ids), "partial blocks contain point 1")
    counts = Counter(t for i in ids for t in combinations(BLOCKS[i], 3))
    for a, b in combinations(range(2, 17), 2):
        require(counts[(1, a, b)] == 1 + ((1, a, b) in excess), "point-one triples met exactly")
    demand = [1 + (t in excess) - counts[t] for t in TRIPLES]
    require(min(demand) >= 0 and sum(demand) == 440, "residual demands")
    zero = {row for row, d in enumerate(demand) if d == 0}
    kept = [j for j, rows in COLUMN_ROWS.items() if not zero.intersection(rows)]
    rhs = {row: d for row, d in enumerate(demand) if d > 0}
    rhs[SUM_ROW] = 44
    return rhs, kept


def margin(y, rhs, kept):
    """Exact b.y - sum_j max(0, (A^T y)_j) for an integer or Fraction vector y."""
    total = sum(value * y.get(row, 0) for row, value in rhs.items())
    for j in kept:
        s = y.get(SUM_ROW, 0) + sum(y.get(row, 0) for row in COLUMN_ROWS[j])
        if s > 0:
            total -= s
    return total


def propose(rhs, kept):
    """Solve max b.y - sum w, A^T y <= w, w >= 0, -1 <= y <= 1 with GLOP."""
    solver = pywraplp.Solver.CreateSolver("GLOP")
    y = {row: solver.NumVar(-1, 1, f"y{row}") for row in rhs}
    objective = solver.Objective()
    for row, value in rhs.items():
        objective.SetCoefficient(y[row], value)
    for j in kept:
        w = solver.NumVar(0, solver.infinity(), f"w{j}")
        objective.SetCoefficient(w, -1)
        constraint = solver.Constraint(-solver.infinity(), 0)
        constraint.SetCoefficient(w, -1)
        constraint.SetCoefficient(y[SUM_ROW], 1)
        for row in COLUMN_ROWS[j]:
            if row in y:
                constraint.SetCoefficient(y[row], 1)
    objective.SetMaximization()
    status = solver.Solve()
    if status != pywraplp.Solver.OPTIMAL:
        return None, None
    return {row: var.solution_value() for row, var in y.items()}, objective.Value()


def certify(rhs, kept):
    values, lp_value = propose(rhs, kept)
    if values is None or lp_value <= 1e-7:
        return None, lp_value
    for bound in DENOMINATORS:
        fractions = {
            row: Fraction(v).limit_denominator(bound) for row, v in values.items() if abs(v) > 1e-12
        }
        fractions = {row: v for row, v in fractions.items() if v}
        if not fractions:
            continue
        scale = lcm(*(v.denominator for v in fractions.values()))
        integers = {row: int(v * scale) for row, v in fractions.items()}
        value = margin(integers, rhs, kept)
        if value > 0:
            return {"y": sorted(integers.items()), "margin": value}, lp_value
    return None, lp_value


def init_worker():
    CONTEXT.update(load_context())


def evaluate(case):
    started = time.perf_counter()
    ids = partial_ids(CONTEXT, case["catalog"], case["partial_id"])
    rhs, kept = build_system(ids, CONTEXT["excess"][case["profile_id"]])
    certificate, lp_value = certify(rhs, kept)
    record = {
        **case,
        "eligible": len(kept),
        "positive_rows": len(rhs) - 1,
        "lp_value": lp_value,
        "seconds": time.perf_counter() - started,
    }
    if certificate:
        record["outcome"] = "lp_farkas_exclusion"
        record["certificate"] = certificate
    else:
        record["outcome"] = "no_lp_certificate"
    return record


def read_cases(limit=None):
    cases = []
    for catalog, (path, expected, count) in STREAMS.items():
        require(digest(path) == expected, f"pinned survivor stream {catalog}")
        with gzip.open(path, "rt") as handle:
            rows = [json.loads(line) for line in handle]
        require(len(rows) == count, f"complete {catalog} survivor stream")
        identities = {(r["pair_ordinal"], r["partial_id"], r["profile_id"]) for r in rows}
        require(len(identities) == count, f"distinct {catalog} survivors")
        cases.extend(
            {
                "catalog": catalog,
                "pair_ordinal": r["pair_ordinal"],
                "partial_id": r["partial_id"],
                "profile_id": r["profile_id"],
            }
            for r in rows
        )
    return cases[:limit] if limit else cases


def run(args):
    raw = Path(args.raw)
    raw.mkdir(parents=True, exist_ok=False)
    cases = read_cases(args.limit)
    manifest = {
        "source_sha256": digest(__file__),
        "input_pins": {str(p.relative_to(ROOT)): h for p, h in PINS.items()},
        "streams": {k: [str(v[0].relative_to(ROOT)), v[1], v[2]] for k, v in STREAMS.items()},
        "cases": len(cases),
        "workers": args.workers,
        "python": platform.python_version(),
        "ortools": ORTOOLS_VERSION,
        "optimizer_role": "GLOP proposes duals only; exact integer arithmetic decides",
    }
    (raw / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    outcomes = Counter()
    started = time.monotonic()
    open_cases = []
    with (
        get_context("spawn").Pool(args.workers, initializer=init_worker) as pool,
        gzip.open(raw / "certificates.jsonl.gz", "wt", compresslevel=6) as out,
    ):
        for done, record in enumerate(pool.imap(evaluate, cases, chunksize=64), 1):
            outcomes[(record["catalog"], record["outcome"])] += 1
            out.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
            if record["outcome"] != "lp_farkas_exclusion":
                open_cases.append(record)
            if done % 10000 == 0:
                rate = done / (time.monotonic() - started)
                print(f"{done}/{len(cases)} {dict(outcomes)} {rate:.0f}/s", flush=True)
    result = {
        "cases": len(cases),
        "complete": True,
        "elapsed_seconds": time.monotonic() - started,
        "outcomes": {f"{k[0]}:{k[1]}": v for k, v in sorted(outcomes.items())},
        "open_cases": open_cases,
        "certificates_sha256": digest(raw / "certificates.jsonl.gz"),
        "manifest_sha256": digest(raw / "manifest.json"),
    }
    (raw / "result.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "open_cases"}), flush=True)
    print("open cases:", len(open_cases), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--limit", type=int)
    run(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
