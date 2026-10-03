#!/usr/bin/env python3
# Document:    Independent Double-Hub Dual Certificate Checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      85271637c6c9eab959e2add62c7388b86d97c21b01412922946f1245efdbeb60
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Replay exact covering duals with only Python's standard library.

The trusted input is the prescribed 32-block family, not any LP status.
Nonnegative weights on its missing triples with every 5-block load <=1
sum to a lower bound on the number of additional blocks in any completion.
"""

import argparse
import copy
import gzip
import hashlib
import json
import math
from fractions import Fraction
from itertools import combinations
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


BLOCKS = list(combinations(range(1, 17), 5))
TRIPLES = list(combinations(range(1, 17), 3))
TRIPLE_IDS = {t: i for i, t in enumerate(TRIPLES)}
ROWS = [tuple(TRIPLE_IDS[t] for t in combinations(b, 3)) for b in BLOCKS]
ALLOWED = [i for i, b in enumerate(BLOCKS) if 1 not in b and 2 not in b]


def ids(value, limit, length=None):
    require(isinstance(value, list), "IDs must be a list")
    require(all(type(i) is int and 0 <= i < limit for i in value), "invalid ID")
    require(value == sorted(set(value)), "IDs must be ordered and distinct")
    require(length is None or len(value) == length, "wrong ID count")
    return value


def check_case(seed, case):
    require(case["identifier"] == seed["identifier"], "case identifier mismatch")
    require(case["first_class"] == seed["first_class"], "first class mismatch")
    retained = ids(case["retained_block_ids"], len(BLOCKS), 32)
    require(retained == seed["retained_block_ids"], "retained input mismatch")
    require(
        seed["retained_blocks"] == [list(BLOCKS[i]) for i in retained], "retained labels mismatch"
    )
    covered = {t for b in retained for t in ROWS[b]}
    missing = sorted(set(range(len(TRIPLES))) - covered)
    cert = case["certificate"]
    require(cert["missing_triples"] == missing, "missing triple mismatch")
    weights = cert["weights"]
    require(isinstance(weights, list), "weights must be a list")
    seen = set()
    values = {}
    for row in weights:
        require(isinstance(row, list) and len(row) == 3, "malformed weight")
        t, n, d = row
        require(all(type(x) is int for x in row), "noninteger rational weight")
        require(t in missing and t not in seen, "duplicate or nonmissing weight")
        require(n >= 0 and d > 0, "invalid rational weight")
        seen.add(t)
        values[t] = Fraction(n, d)
    scale = math.lcm(*(v.denominator for v in values.values()))
    loads = [int(values.get(t, 0) * scale) for t in range(len(TRIPLES))]
    maximum = max(sum(loads[t] for t in row) for row in ROWS)
    require(maximum <= scale, "block capacity exceeded")
    bound = Fraction(sum(loads), scale)
    reported = cert["lower_bound"]
    require(
        isinstance(reported, list)
        and len(reported) == 2
        and all(type(x) is int for x in reported)
        and reported[1] > 0,
        "malformed reported lower bound",
    )
    require(bound == Fraction(*reported), "lower bound mismatch")
    require(
        type(case["excluded"]) is bool and case["excluded"] == (bound > 32),
        "exclusion flag mismatch",
    )
    return {
        "identifier": case["identifier"],
        "missing_count": len(missing),
        "lower_bound": [bound.numerator, bound.denominator],
        "maximum_load": [maximum, scale],
        "excluded": bound > 32,
    }


def check_archive(seeds, certificate, input_sha256):
    meta = certificate["metadata"]
    require(meta["input_sha256"] == input_sha256, "input SHA256 mismatch")
    require(
        type(meta["additional_budget"]) is int and meta["additional_budget"] == 32,
        "wrong addition budget",
    )
    require(meta["allowed_block_ids"] == ALLOWED, "allowed pool mismatch")
    candidates = seeds["candidates"]
    cases = certificate["cases"]
    require(len(candidates) == len(cases) and len(cases) > 0, "case count mismatch")
    require(len({s["identifier"] for s in candidates}) == len(cases), "duplicate seed case")
    results = []
    for i, (seed, case) in enumerate(zip(candidates, cases, strict=True)):
        require(type(case["case"]) is int and case["case"] == i, "case index mismatch")
        results.append(check_case(seed, case))
    return results


def damage_controls(seed, case):
    changes = {
        "duplicate_retained": lambda c: c["retained_block_ids"].__setitem__(
            1, c["retained_block_ids"][0]
        ),
        "changed_case_identity": lambda c: c.__setitem__("identifier", "damaged"),
        "missing_triple_removed": lambda c: c["certificate"]["missing_triples"].pop(),
        "duplicate_weight": lambda c: c["certificate"]["weights"].append(
            c["certificate"]["weights"][0]
        ),
        "negative_weight": lambda c: c["certificate"]["weights"][0].__setitem__(1, -1),
        "zero_denominator": lambda c: c["certificate"]["weights"][0].__setitem__(2, 0),
        "noninteger_weight": lambda c: c["certificate"]["weights"][0].__setitem__(1, 1.5),
        "capacity_exceeded": lambda c: c["certificate"]["weights"][0].__setitem__(1, 2000001),
        "wrong_bound": lambda c: c["certificate"].__setitem__("lower_bound", [0, 1]),
        "wrong_exclusion": lambda c: c.__setitem__("excluded", not c["excluded"]),
        "weight_on_covered": lambda c: c["certificate"]["weights"][0].__setitem__(
            0, ROWS[c["retained_block_ids"][0]][0]
        ),
    }
    passed = []
    for name, change in changes.items():
        damaged = copy.deepcopy(case)
        change(damaged)
        try:
            check_case(seed, damaged)
        except (ValueError, KeyError, TypeError):
            passed.append(name)
        else:
            raise ValueError(f"damaged control accepted: {name}")
    return passed


def load(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw), hashlib.sha256(
        raw
    ).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seeds", type=Path)
    parser.add_argument("certificate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    seeds, seed_hash = load(args.seeds)
    certificate, cert_hash = load(args.certificate)
    cases = check_archive(seeds, certificate, seed_hash)
    controls = damage_controls(seeds["candidates"][0], certificate["cases"][0])
    # Archive-level controls exercise binding, ordering and budget validation.
    for field, value in [
        ("input_sha256", "0" * 64),
        ("additional_budget", 31),
        ("allowed_block_ids", ALLOWED[:-1]),
    ]:
        damaged = copy.deepcopy(certificate)
        damaged["metadata"][field] = value
        try:
            check_archive(seeds, damaged, seed_hash)
        except ValueError:
            controls.append(field)
        else:
            raise ValueError(f"archive damage accepted: {field}")
    result = {
        "input_sha256": seed_hash,
        "certificate_sha256": cert_hash,
        "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "checked_cases": len(cases),
        "capacity_blocks_per_case": len(BLOCKS),
        "damage_controls_rejected": controls,
        "cases": cases,
        "excluded": [c["identifier"] for c in cases if c["excluded"]],
        "scope": "Any completion retaining the prescribed32 blocks; not a global bound.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}))


if __name__ == "__main__":
    main()
