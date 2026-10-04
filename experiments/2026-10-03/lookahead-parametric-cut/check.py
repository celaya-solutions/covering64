# Document:    Independent Exact Parametric Heavy-Cut Checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      8d1314de0eefe84ff284912b49c0895971eeafa84b28cfd194524f44b6cdf85d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Pure-Python replay: no solver, model builder or cut deriver is imported."""

import copy
import hashlib
import itertools as it
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "lookahead-heavy-strengthened"
GATE = HERE.parent / "native-ten-hole-completion-independent"
ANCHORS = [(1, 2, 3), (5, 6, 7), (9, 10, 11), (13, 14, 15)]
HUBS = (4, 8, 12, 16)
POINTS = tuple(range(1, 17))
TRIPLES = list(it.combinations(POINTS, 3))
PAIRS = list(it.combinations(POINTS, 2))


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pair_bounds(pair):
    for g, anchor in enumerate(ANCHORS):
        inside = set(pair).intersection(anchor)
        if len(inside) == 2:
            return 7, 7
        if inside:
            other = next(p for p in pair if p not in anchor)
            value = 6 if other == HUBS[g] else 5
            return value, value
    return 5, 7


def family_proof():
    # Necessary pair lower bounds saturate every degree20 anchor point.
    require(3 * 5 - 2 < 14 <= 3 * 6 - 2, "own-hub repeated triples")
    for point in POINTS:
        if point not in HUBS:
            require(sum(pair_bounds(p)[0] for p in PAIRS if point in p) == 80, "anchor saturation")
    hpairs = list(it.combinations(HUBS, 2))
    graphs = [
        v
        for v in it.product(range(3), repeat=6)
        if all(sum(v[i] for i, p in enumerate(hpairs) if h in p) == 2 for h in HUBS)
    ]
    require(len(graphs) == 6, "six hub graphs")
    for hub in HUBS:
        require(
            sum(pair_bounds(p)[0] for p in PAIRS if hub in p and p not in hpairs) == 63,
            "hub anchor contribution",
        )
    require(80 - 63 - 3 * 5 == 2, "hub residual degree")
    fixed = 0
    for triple in TRIPLES:
        if triple in ANCHORS:
            continue
        groups = [g for g, a in enumerate(ANCHORS) if len(set(triple).intersection(a)) == 2]
        if groups:
            require(len(groups) == 1, "one repeated anchor group")
            # The own template covers each external point once, or its own hub twice.
            g = groups[0]
            other = next(p for p in triple if p not in ANCHORS[g])
            require((2 if other == HUBS[g] else 1) <= 2, "fixed triple cap")
            fixed += 1
        else:
            for graph in graphs:
                targets = {p: pair_bounds(p)[0] for p in PAIRS}
                targets.update({p: 5 + graph[i] for i, p in enumerate(hpairs)})
                require(
                    any(targets[p] == 5 for p in it.combinations(triple, 2)),
                    "triple has a multiplicity5 pair",
                )
    require(fixed == 156, "fixed nonheavy triples")
    return graphs


def replay(cut, dual):
    denominator = dual["denominator"]
    require(type(denominator) is int and denominator > 0, "denominator")
    entries = dual["weights"]
    require(
        all(
            isinstance(e, list)
            and len(e) == 2
            and type(e[0]) is int
            and type(e[1]) is int
            and 0 <= e[0] < 697
            and e[1] != 0
            for e in entries
        ),
        "signed row format",
    )
    require(
        entries == sorted(entries) and len({e[0] for e in entries}) == len(entries),
        "signed row identities",
    )
    weights = dict(entries)
    triple_weights = {t: weights.get(i + 1, 0) for i, t in enumerate(TRIPLES)}
    point_weights = {p: weights.get(560 + p, 0) for p in POINTS}
    pair_weights = {p: weights.get(577 + i, 0) for i, p in enumerate(PAIRS)}
    constant = 64 * weights.get(0, 0) + 20 * sum(point_weights.values())
    for triple, weight in triple_weights.items():
        require(not (triple in ANCHORS and weight < 0), "unbounded upper multiplier")
        constant += weight * (1 if weight >= 0 else 2)
    for pair, weight in pair_weights.items():
        low, high = pair_bounds(pair)
        constant += weight * (low if weight >= 0 else high)

    def coefficient(block):
        return (
            weights.get(0, 0)
            + sum(point_weights[p] for p in block)
            + sum(triple_weights[t] for t in it.combinations(block, 3))
            + sum(pair_weights[p] for p in it.combinations(block, 2))
        )

    universe = list(it.combinations(POINTS, 5))
    global_ids = {b: i for i, b in enumerate(universe)}
    ordinary = [b for b in universe if all(len(set(b).intersection(a)) < 2 for a in ANCHORS)]
    # Construct heavy candidates anchor-by-anchor from all legal external edges.
    heavy = []
    for g, anchor in enumerate(ANCHORS):
        outside = [p for p in POINTS if p not in anchor]
        candidates = [
            tuple(sorted((*anchor, *edge)))
            for edge in it.combinations(outside, 2)
            if not any(set(edge) <= set(a) for j, a in enumerate(ANCHORS) if j != g)
        ]
        require(len(candidates) == 69, "complete heavy group")
        heavy.extend(candidates)
    heavy.sort()
    require(len(ordinary) == 1200 and len(heavy) == len(set(heavy)) == 276, "universes")
    coefficients = [coefficient(b) for b in heavy]
    columns = [coefficient(b) for b in ordinary]
    box = sum(c for c in columns if c > 0)
    threshold = constant - box
    require(cut["direction"] == ">=", "cut direction")
    require(cut["heavy_blocks"] == list(map(list, heavy)), "heavy blocks")
    require(cut["heavy_global_ids"] == [global_ids[b] for b in heavy], "heavy IDs")
    require(cut["ordinary_global_ids"] == [global_ids[b] for b in ordinary], "ordinary IDs")
    require(cut["coefficients"] == coefficients, "heavy coefficients")
    require(cut["ordinary_combined_coefficients"] == columns, "ordinary coefficients")
    require(cut["constant_numerator"] == constant, "constant")
    require(cut["ordinary_box_max_numerator"] == box == dual["box_max_numerator"], "box maximum")
    require(cut["rhs"] == threshold and cut["denominator"] == denominator, "cut bound")
    seed_path = HERE.parent / "lookahead-heavy-completion/seed.txt"
    seed = [tuple(map(int, line.split())) for line in seed_path.read_text().splitlines()]
    seed_heavy = sorted(set(seed).intersection(heavy))
    require(len(seed_heavy) == 28, "seed heavy count")
    lhs = sum(coefficient(b) for b in seed_heavy)
    require(cut["seed_heavy_global_ids"] == [global_ids[b] for b in seed_heavy], "seed heavy IDs")
    require(cut["seed_lhs"] == lhs, "seed LHS")
    require(constant - lhs == dual["rhs_numerator"], "fixed tuple dual RHS")
    gap = Fraction(threshold - lhs, denominator)
    require(gap > 0 and dual["gap"] == [gap.numerator, gap.denominator], "exact positive gap")
    require(dual["proves_infeasible"] is True, "proof flag")
    require(cut["seed_violation_numerator"] == threshold - lhs, "violation")
    require(cut["seed_sha256"] == sha(seed_path), "seed hash")
    return {
        "rhs": threshold,
        "seed_lhs": lhs,
        "violation_numerator": threshold - lhs,
        "denominator": denominator,
        "gap": [gap.numerator, gap.denominator],
        "signed_rows": len(entries),
        "ordinary_box_max_numerator": box,
        "heavy_coefficient_range": [min(coefficients), max(coefficients)],
    }


def main():
    cut_path, dual_path = HERE / "cut.json", SOURCE / "dual.json"
    cut, dual = json.loads(cut_path.read_text()), json.loads(dual_path.read_text())
    gate_path = GATE / "dual-audit.json"
    gate = json.loads(gate_path.read_text())
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    require(gate["passed"] and gate["dual_sha256"] == sha(dual_path), "source dual gate")
    require(gate["checker_sha256"] == sha(GATE / "check_dual.py"), "source checker hash")
    require(gate["model_sha256"] == sha(ROOT / manifest["model"]), "source model hash")
    require(cut["dual_sha256"] == sha(dual_path), "cut dual hash")
    require(cut["source_gate_sha256"] == sha(gate_path), "cut gate hash")
    require(cut["source_model_sha256"] == gate["model_sha256"], "cut model hash")
    require(cut["deriver_sha256"] == sha(HERE / "derive.py"), "deriver hash")
    map_path = HERE / "row-map.json"
    require(cut["row_map_sha256"] == sha(map_path), "row map hash")
    row_map = json.loads(map_path.read_text())
    require(row_map["dual_sha256"] == sha(dual_path), "row map dual hash")
    require(row_map["ordinary_domain"] == [0, 1], "row map domain")
    subsets = [()] + TRIPLES + [(p,) for p in POINTS] + PAIRS
    kinds = ["cardinality"] + ["triple"] * 560 + ["point"] * 16 + ["pair"] * 120
    bounds = [(64, 64)] + [(1, None if t in ANCHORS else 2) for t in TRIPLES]
    bounds += [(20, 20)] * 16 + [pair_bounds(p) for p in PAIRS]
    w = dict(dual["weights"])
    expected_map = [
        {
            "index": i,
            "kind": kind,
            "subset": list(subset),
            "lower": bound[0],
            "upper": bound[1],
            "weight": w.get(i, 0),
        }
        for i, (subset, kind, bound) in enumerate(zip(subsets, kinds, bounds, strict=True))
    ]
    require(row_map["rows"] == expected_map, "symbolic row map")
    graphs = family_proof()
    result = replay(cut, dual)
    controls = []
    for key in [
        "rhs",
        "constant_numerator",
        "ordinary_box_max_numerator",
        "denominator",
        "seed_lhs",
        "seed_violation_numerator",
    ]:
        bad = copy.deepcopy(cut)
        bad[key] += 1
        controls.append((key, bad, dual))
    for key in [
        "coefficients",
        "heavy_global_ids",
        "ordinary_global_ids",
        "ordinary_combined_coefficients",
        "seed_heavy_global_ids",
    ]:
        bad = copy.deepcopy(cut)
        bad[key][0] += 1
        controls.append((key, bad, dual))
    bad = copy.deepcopy(cut)
    bad["direction"] = "<="
    controls.append(("direction", bad, dual))
    bad = copy.deepcopy(cut)
    bad["heavy_blocks"].pop()
    controls.append(("missing heavy candidate", bad, dual))
    bad_dual = copy.deepcopy(dual)
    bad_dual["weights"].append(bad_dual["weights"][0])
    controls.append(("duplicate dual row", cut, bad_dual))
    bad_dual = copy.deepcopy(dual)
    bad_dual["weights"][0][1] += 1
    controls.append(("altered dual weight", cut, bad_dual))
    rejected = []
    for label, candidate, certificate in controls:
        try:
            replay(candidate, certificate)
        except (ValueError, KeyError, IndexError, TypeError):
            rejected.append(label)
        else:
            raise AssertionError(f"damage accepted: {label}")
    result.update(
        {
            "passed": True,
            "checker_sha256": sha(Path(__file__)),
            "cut_sha256": sha(cut_path),
            "dual_sha256": sha(dual_path),
            "source_gate_sha256": sha(gate_path),
            "row_map_sha256": sha(map_path),
            "heavy_variables": 276,
            "ordinary_variables": 1200,
            "hub_graphs": [list(v) for v in graphs],
            "damaged_controls_rejected": len(rejected),
            "damage_controls": rejected,
            "scope": cut["scope"],
        }
    )
    (HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
