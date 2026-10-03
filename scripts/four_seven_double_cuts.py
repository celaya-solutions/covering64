# Document:    Four Sevenfold Triple Double Multiplicity Lift
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Integer full-cover consequences in the normalized four-sevenfold branch."""

from fractions import Fraction
from itertools import combinations

from ortools.sat.python import cp_model

ANCHORS = tuple(tuple(range(4 * i + 1, 4 * i + 4)) for i in range(4))
HUBS = (4, 8, 12, 16)
LOW, HIGH = -(2**63), 2**63 - 1


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pair_targets(case):
    require(case in ("cycle", "matching"), "unknown hub pair case")
    result = {pair: 5 for pair in combinations(range(1, 17), 2)}
    for anchors, hub in zip(ANCHORS, HUBS):
        for pair in combinations(anchors, 2):
            result[pair] = 7
        for p in anchors:
            result[tuple(sorted((p, hub)))] = 6
    edges = ((4, 8), (12, 16))
    if case == "cycle":
        edges += ((8, 12), (4, 16))
    for edge in edges:
        result[edge] += 1 if case == "cycle" else 2
    return result


def classify_triples(universe):
    eligible, fixed, heavy = [], {}, []
    for i, triple in enumerate(universe.triples):
        sizes = [len(set(triple).intersection(group)) for group in ANCHORS]
        if 3 in sizes:
            heavy.append(i)
        elif 2 in sizes:
            group = sizes.index(2)
            fixed[i] = 2 if HUBS[group] in triple else 1
        else:
            eligible.append(i)
    require((len(eligible), len(fixed), len(heavy)) == (400, 156, 4), "wrong triple partition")
    return eligible, fixed, heavy


def double_pair_targets(case):
    targets = pair_targets(case)
    result = {}
    for pair, value in targets.items():
        same_group = any(set(pair).issubset(group) for group in ANCHORS)
        own_hub = any(hub in pair and bool(set(pair).intersection(group))
                      for group, hub in zip(ANCHORS, HUBS))
        if same_group:
            result[pair] = 0
        elif own_hub:
            result[pair] = 2
        elif set(pair).issubset(HUBS):
            result[pair] = 3 * value - 14
        else:
            result[pair] = 1
    return result


def validate_full_branch(universe, model, xs, case):
    require((universe.v, universe.k, universe.t) == (16, 5, 3), "wrong universe")
    require(len(xs) == 4368, "all block variables required")
    for i, x in enumerate(xs):
        require(x.index == i and x.name == f"block_{i}", "wrong lexicographic variable order")
        require(tuple(model.proto.variables[i].domain) == (0, 1), "block is not Boolean")
    rows = {
        (tuple(sorted(zip(c.linear.vars, c.linear.coeffs))), tuple(c.linear.domain))
        for c in model.proto.constraints if c.has_linear() and not c.enforcement_literal
    }

    def has(ids, lower, upper):
        return (tuple((i, 1) for i in sorted(ids)), (lower, upper)) in rows

    allowed = [i for i, b in enumerate(universe.blocks)
               if all(len(set(b).intersection(group)) != 2 for group in ANCHORS)]
    allowed_set = set(allowed)
    for i in range(4368):
        if i not in allowed_set:
            require(has([i], 0, 0), "missing forbidden-block row")
    require(has(range(4368), 64, 64), "missing cardinality row")
    for p in range(1, 17):
        require(has([i for i in allowed if p in universe.blocks[i]], 20, 20),
                "missing regular degree")
    for pair, target in pair_targets(case).items():
        require(has([i for i in allowed if set(pair).issubset(universe.blocks[i])], target, target),
                "missing or wrong pair target")
    for triple in ANCHORS:
        require(has([i for i in allowed if set(triple).issubset(universe.blocks[i])], 7, 7),
                "missing sevenfold row")
    for containing in universe.containing:
        require(has([i for i in containing if i in allowed_set], 1, HIGH),
                "full unconditional coverage is required")


def add_double_triple_cuts(universe, model, xs, case):
    """Append400 Boolean double flags and677 rows; preserve every prior field."""
    validate_full_branch(universe, model, xs, case)
    require(not any(v.name.startswith("double_triple_") for v in model.proto.variables),
            "double lift already present")
    eligible, fixed, _ = classify_triples(universe)
    before = len(model.proto.variables), len(model.proto.constraints)
    doubles = {}
    for tid in eligible:
        double = model.new_bool_var(f"double_triple_{tid}")
        doubles[tid] = double
        model.add(sum(xs[i] for i in universe.containing[tid]) == 1 + double)
    for tid, count in fixed.items():
        model.add(sum(xs[i] for i in universe.containing[tid]) == count)
    model.add(sum(doubles.values()) == 44)
    for pair, demand in double_pair_targets(case).items():
        terms = [double for tid, double in doubles.items()
                 if set(pair).issubset(universe.triples[tid])]
        # Keep a linear 0=0 row for the12 internal pairs as explicit arithmetic controls.
        model.add_linear_constraint(cp_model.LinearExpr.sum(terms), demand, demand)
        last = len(model.proto.constraints) - 1
        if not terms and not model.proto.constraints[last].has_linear():
            model.proto.constraints[last].linear.domain.extend([demand, demand])
    return doubles, {
        "case": case, "new_variables": len(model.proto.variables) - before[0],
        "new_rows": len(model.proto.constraints) - before[1],
        "eligible_triples": len(eligible),
        "fixed_double_triples": sum(v == 2 for v in fixed.values()),
        "fixed_single_triples": sum(v == 1 for v in fixed.values()),
        "pair_rows": 120, "scope": "Only normalized regular full four-sevenfold covers.",
    }


def fractional_double_values(universe, weights):
    """Extend a fractional LP witness; these are NOT CP-SAT hint values."""
    require(len(weights) == len(universe.blocks), "wrong fractional vector length")
    eligible, fixed, heavy = classify_triples(universe)
    counts = {tid: sum((Fraction(weights[i]) for i in universe.containing[tid]), Fraction(0))
              for tid in range(len(universe.triples))}
    require(all(counts[tid] == value for tid, value in fixed.items()),
            "fractional witness violates integer-derived fixed triples")
    require(all(counts[tid] == 7 for tid in heavy), "wrong heavy multiplicity")
    values = {f"double_triple_{tid}": counts[tid] - 1 for tid in eligible}
    require(all(0 <= value <= 1 for value in values.values()), "double value outside0..1")
    return values
