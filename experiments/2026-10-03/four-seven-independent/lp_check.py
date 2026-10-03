# Document:    Independent Rational Four Sevenfold Witness Recount
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      1338f5237e487ab904276df9c84c5b45b75269ed508dcc0dc76d2c5f4b739a85
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import argparse
import collections
import copy
import hashlib
import itertools
import json
import pathlib
from fractions import Fraction

GROUPS = [(1, 2, 3), (5, 6, 7), (9, 10, 11), (13, 14, 15)]
HUBS = [4, 8, 12, 16]
BLOCKS = list(itertools.combinations(range(1, 17), 5))
TRIPLES = list(itertools.combinations(range(1, 17), 3))
PAIRS = list(itertools.combinations(range(1, 17), 2))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pair_targets(case):
    require(case in {"cycle", "matching"}, "unknown branch")
    targets = dict.fromkeys(PAIRS, 5)
    for group, hub in zip(GROUPS, HUBS, strict=True):
        for pair in itertools.combinations(group, 2):
            targets[pair] = 7
        for anchor in group:
            targets[tuple(sorted((anchor, hub)))] = 6
    hub_edges = [(4, 8), (8, 12), (12, 16), (4, 16)] if case == "cycle" else [(4, 8), (12, 16)]
    for pair in hub_edges:
        targets[pair] += 1 if case == "cycle" else 2
    return targets


def verify(document):
    weights = {}
    for index, numerator, denominator in document["nonzero_weights"]:
        require(
            type(index) is int and 0 <= index < 4368 and index not in weights, "invalid block index"
        )
        require(
            type(numerator) is int and type(denominator) is int and denominator > 0,
            "invalid rational weight",
        )
        value = Fraction(numerator, denominator)
        require(0 < value <= 1, "weight outside Boolean relaxation")
        weights[index] = value
    require(sum(weights.values()) == 64, "total block weight")
    points, pairs, triples = collections.Counter(), collections.Counter(), collections.Counter()
    for index, value in weights.items():
        block = BLOCKS[index]
        require(all(len(set(block) & set(group)) != 2 for group in GROUPS), "forbidden block")
        for point in block:
            points[point] += value
        for pair in itertools.combinations(block, 2):
            pairs[pair] += value
        for triple in itertools.combinations(block, 3):
            triples[triple] += value
    require(all(points[p] == 20 for p in range(1, 17)), "point degree")
    targets = pair_targets(document["case"])
    require(pairs == targets, "pair targets")
    require(all(triples[t] >= 1 for t in TRIPLES), "uncovered fractional triple")
    require(all(triples[group] == 7 for group in GROUPS), "heavy triple count")
    fixed = {}
    for group, hub in zip(GROUPS, HUBS, strict=True):
        for pair in itertools.combinations(group, 2):
            for outside in range(1, 17):
                if outside not in group:
                    fixed[tuple(sorted((*pair, outside)))] = 2 if outside == hub else 1
    require(len(fixed) == 156, "fixed triple classification")
    wrong = [
        dict(triple=t, actual=str(triples[t]), required=value)
        for t, value in fixed.items()
        if triples[t] != value
    ]
    transversal = [t for t in TRIPLES if all(len(set(t) & set(group)) <= 1 for group in GROUPS)]
    require(len(transversal) == 400, "transversal triple universe")
    delta = {t: triples[t] - 1 for t in transversal}
    demand = {}
    for pair in PAIRS:
        if any(set(pair) <= set(group) for group in GROUPS):
            demand[pair] = 0
        elif all(p in HUBS for p in pair):
            demand[pair] = 3 * targets[pair] - 14
        else:
            own_hub = any(
                h in pair and any(a in pair for a in group)
                for group, h in zip(GROUPS, HUBS, strict=True)
            )
            demand[pair] = 2 if own_hub else 1
    mismatch = [
        dict(
            pair=pair,
            actual=str(sum(v for t, v in delta.items() if set(pair) <= set(t))),
            required=required,
        )
        for pair, required in demand.items()
        if sum(v for t, v in delta.items() if set(pair) <= set(t)) != required
    ]
    if not wrong:
        require(
            all(0 <= value <= 1 for value in delta.values()) and sum(delta.values()) == 44,
            "fractional double-triple weights",
        )
        require(not mismatch, "fractional triangle demands")
    return dict(
        nonzero_block_weights=len(weights),
        all_4368_domains_checked=True,
        block_weight="64",
        point_degrees=[str(points[p]) for p in range(1, 17)],
        all_120_pair_targets_checked=True,
        all_560_coverage_bounds_checked=True,
        all_four_heavy_triples_checked=True,
        fixed156_violations=wrong,
        satisfies_fixed156=not wrong,
        fractional_double_system_verified=not wrong,
        double_weight=str(sum(delta.values())),
        double_demand_mismatches=mismatch,
        nonzero_double_weights=[
            dict(triple=t, value=str(value)) for t, value in delta.items() if value
        ],
        triple_weight_histogram=dict(collections.Counter(str(triples[t]) for t in TRIPLES)),
        integral_blocks=all(value.denominator == 1 for value in weights.values()),
        integral_double_system=all(value.denominator == 1 for value in delta.values()),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("witness", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()
    document = json.loads(args.witness.read_text())
    result = verify(document)
    controls = []
    for label in ["wrong weight", "missing block", "wrong branch", "duplicate index"]:
        damaged = copy.deepcopy(document)
        if label == "wrong weight":
            damaged["nonzero_weights"][0][1] += damaged["nonzero_weights"][0][2]
        elif label == "missing block":
            damaged["nonzero_weights"].pop()
        elif label == "wrong branch":
            damaged["case"] = "cycle" if document["case"] == "matching" else "matching"
        else:
            damaged["nonzero_weights"].append(damaged["nonzero_weights"][0])
        try:
            verify(damaged)
        except ValueError:
            controls.append(dict(control=label, rejected=True))
        else:
            raise ValueError("damaged rational witness accepted")
    result.update(
        complete=True,
        case=document["case"],
        witness=str(args.witness),
        witness_sha256=hashlib.sha256(args.witness.read_bytes()).hexdigest(),
        checker_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        damaged_controls=controls,
        scope="Exact rational recount; fractional feasibility does not establish an integer cover.",
    )
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: result[key]
                for key in [
                    "case",
                    "complete",
                    "satisfies_fixed156",
                    "fractional_double_system_verified",
                    "double_weight",
                    "integral_blocks",
                    "integral_double_system",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
