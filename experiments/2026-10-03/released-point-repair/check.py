# Document:    Independent Released Point Dual Certificate Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Rebuild the complete neighborhood with itertools and check integer inequalities."""

import argparse
import copy
import gzip
import hashlib
import json
from fractions import Fraction
from itertools import combinations
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value):
    return type(value) is int


def check(initial, metadata, dual):
    rows = [line.split() for line in initial.splitlines() if line.strip()]
    require(len(rows) == 64, "input must have exactly 64 blocks")
    blocks = [tuple(int(value) for value in row) for row in rows]
    require(all(len(b) == 5 and tuple(sorted(set(b))) == b
                and all(1 <= p <= 16 for p in b) for b in blocks), "malformed block")
    require(len(set(blocks)) == 64, "duplicate block")
    universe = list(combinations(range(1, 17), 5))
    triples = list(combinations(range(1, 17), 3))
    ranks = {b: i for i, b in enumerate(universe)}
    triple_ranks = {t: i for i, t in enumerate(triples)}
    points = metadata["release_points"]
    require(points and all(integer(p) and 1 <= p <= 16 for p in points)
            and points == sorted(set(points)), "bad release points")
    points = set(points)
    selected = {ranks[b] for b in blocks}
    retained = sorted(i for i in selected if not points.intersection(universe[i]))
    candidates = [i for i, b in enumerate(universe) if points.intersection(b)]
    coverage = [{triple_ranks[t] for t in combinations(b, 3)} for b in universe]
    covered = {t for i in retained for t in coverage[i]}
    deficient = sorted(set(range(560)) - covered)
    budget = 64 - len(retained)
    require(all(isinstance(metadata[key], list) and all(integer(i) for i in metadata[key])
                for key in ("retained_ids", "candidate_ids", "deficient_ids")),
            "malformed scope ids")
    require(metadata["retained_ids"] == retained, "retained scope mismatch")
    require(metadata["candidate_ids"] == candidates, "candidate scope mismatch")
    require(metadata["deficient_ids"] == deficient, "deficient scope mismatch")
    require(integer(metadata["addition_budget"])
            and metadata["addition_budget"] == budget, "budget mismatch")
    denominator = dual["common_denominator"]
    require(integer(denominator) and denominator > 0, "bad denominator")
    weights = dual["weights"]
    require(isinstance(weights, list)
            and all(isinstance(w, list) and len(w) == 2 for w in weights), "bad weights")
    require(all(integer(t) and integer(n) and n >= 0 and t in deficient
                for t, n in weights), "bad weight or support")
    require(weights == sorted(weights) and len({t for t, _ in weights}) == len(weights),
            "duplicate or unordered weights")
    numerators = dict(weights)
    loads = [sum(numerators.get(t, 0) for t in coverage[i]) for i in candidates]
    require(all(load <= denominator for load in loads), "column capacity exceeded")
    numerator = sum(numerators.values())
    bound = Fraction(numerator, denominator)
    require(isinstance(dual["bound"], list) and len(dual["bound"]) == 2
            and all(integer(value) for value in dual["bound"]), "malformed bound")
    require(dual["bound"] == [bound.numerator, bound.denominator], "bound mismatch")
    require(integer(dual["addition_budget"]) and dual["addition_budget"] == budget,
            "certificate budget mismatch")
    require(integer(dual["columns_checked"]) and dual["columns_checked"] == len(candidates),
            "column count mismatch")
    excludes = numerator > budget * denominator
    require(type(dual["proves_neighborhood_infeasible"]) is bool
            and dual["proves_neighborhood_infeasible"] == excludes, "exclusion mismatch")
    full_coverage = {t for i in selected for t in coverage[i]}
    return {
        "certificate_valid": True,
        "proves_neighborhood_infeasible": excludes,
        "bound": [bound.numerator, bound.denominator],
        "retained_count": len(retained), "candidate_count": len(candidates),
        "deficient_count": len(deficient), "addition_budget": budget,
        "maximum_column_numerator": max(loads, default=0),
        "total_weight_numerator": numerator, "common_denominator": denominator,
        "input_missing_triples": [list(triples[t]) for t in sorted(set(range(560))
                                                                   - full_coverage)],
        "scope": "Retain exactly the listed input blocks avoiding the release points; "
        "every added block must touch a release point. No global lower bound.",
    }


def damaged_controls(initial, metadata, dual):
    tests = []

    def add(name, change, target="dual"):
        changed_metadata = copy.deepcopy(metadata)
        changed_dual = copy.deepcopy(dual)
        change(changed_dual if target == "dual" else changed_metadata)
        tests.append((name, initial, changed_metadata, changed_dual))

    add("capacity", lambda d: d["weights"].__setitem__(
        0, [d["weights"][0][0], d["common_denominator"] + 1]))
    add("negative_weight", lambda d: d["weights"][0].__setitem__(1, -1))
    add("duplicate_weight", lambda d: d["weights"].append(d["weights"][0]))
    covered = next(t for t in range(560) if t not in metadata["deficient_ids"])
    add("covered_triple_weight", lambda d: d["weights"].append([covered, 1]))
    add("missing_allowed_block", lambda d: d["candidate_ids"].pop(), "metadata")
    add("missing_retained_block", lambda d: d["retained_ids"].pop(), "metadata")
    add("missing_deficient_triple", lambda d: d["deficient_ids"].pop(), "metadata")
    add("wrong_budget", lambda d: d.__setitem__("addition_budget", 65), "metadata")
    add("wrong_bound", lambda d: d["bound"].__setitem__(0, d["bound"][0] + 1))
    add("wrong_exclusion", lambda d: d.__setitem__(
        "proves_neighborhood_infeasible", not d["proves_neighborhood_infeasible"]))
    lines = initial.strip().splitlines()
    tests.append(("duplicate_input", "\n".join([lines[0]] + lines[:-1]), metadata, dual))
    tests.append(("malformed_input", "\n".join(["0 1 2 3 4"] + lines[1:]), metadata, dual))
    results = {}
    for name, candidate, altered_metadata, altered_dual in tests:
        try:
            check(candidate, altered_metadata, altered_dual)
        except (ValueError, KeyError, TypeError):
            results[name] = "rejected"
        else:
            raise ValueError(f"damaged control accepted: {name}")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dual-name", default="dual.json")
    args = parser.parse_args()
    names = ("initial.txt", "metadata.json", args.dual_name)
    if args.directory.is_file():
        archive = json.loads(gzip.decompress(args.directory.read_bytes()))
        inputs = {name: archive["files"][name] for name in names}
    else:
        inputs = {name: (args.directory / name).read_text() for name in names}
    initial = inputs["initial.txt"]
    metadata = json.loads(inputs["metadata.json"])
    dual = json.loads(inputs[args.dual_name])
    result = check(initial, metadata, dual)
    result["damaged_controls"] = damaged_controls(initial, metadata, dual)
    result["sha256"] = {name: hashlib.sha256(content.encode()).hexdigest()
                        for name, content in inputs.items()}
    result["sha256"]["check.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result["method"] = "stdlib itertools reconstruction; exact integer column inequalities"
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
