# Document:    Independent Pinned Four-Link Regularity Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      5dcce952c161822910f9e5c004f38eff985cb0f65ab2fe75b1ff2ed22c2e99cd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check pinned-profile hypotheses and every inherited LP row without a solver."""

import json
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from itertools import combinations, product
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
INPUT = ROOT / "experiments/2026-10-04/lp-guided-best-lp/manifest.json"
MODEL = ROOT / "experiments/scratch/lp-guided-best-lp-v1.0.0/model.pbtxt"
POINTS = tuple(range(1, 17))
BLOCKS = list(combinations(POINTS, 5))
PAIRS = list(combinations(POINTS, 2))
TRIPLES = list(combinations(POINTS, 3))
INF = 2**63 - 1
DUAL = ROOT / "experiments/2026-10-04/lp-guided-best-lp/dual.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def derive(anchors, hubs, fixed):
    require(len(anchors) == len(hubs) == 4, "four groups and hubs required")
    require(
        all(len(a) == 3 and tuple(sorted(set(a))) == tuple(a) for a in anchors), "malformed anchor"
    )
    flat = [p for a in anchors for p in a]
    require(len(set(flat)) == 12 and set(flat) <= set(POINTS), "anchors must be disjoint")
    require(
        len(set(hubs)) == 4 and set(hubs) == set(POINTS) - set(flat),
        "distinct hubs must be the complement",
    )
    require(len(fixed) == len(set(fixed)) == 28, "28 distinct pinned blocks required")
    require(all(b in BLOCKS for b in fixed), "malformed block")
    aset = list(map(set, anchors))
    links = []
    for a, h in zip(aset, hubs, strict=True):
        link = [b for b in fixed if a <= set(b)]
        require(len(link) == 7, "each anchor must have seven pinned blocks")
        require(sum(h in b for b in link) >= 2, "own hub must appear twice")
        links.append(link)
    require(set().union(*(set(link) for link in links)) == set(fixed), "unassigned pin")

    # Forced duplicates persist after any further blocks are added.
    lower = {}
    duplicate_receipts = {}
    for pair in PAIRS:
        through = [b for b in fixed if set(pair) <= set(b)]
        third = Counter(p for b in through for p in b if p not in pair)
        duplicates = sum(max(0, count - 1) for count in third.values())
        lower[pair] = max(5, len(through), (14 + duplicates + 2) // 3)
        duplicate_receipts[pair] = duplicates
    degree_lower = {p: (sum(lower[pair] for pair in PAIRS if p in pair) + 3) // 4 for p in POINTS}
    require(all(degree_lower[p] >= 20 for p in POINTS), "regularity bound not established")
    require(sum(degree_lower.values()) == 320, "pins already exceed total incidence")

    targets = {}
    for a, h in zip(aset, hubs, strict=True):
        for p in a:
            for q in POINTS:
                if p != q:
                    targets[tuple(sorted((p, q)))] = 7 if q in a else 6 if q == h else 5
    require(len(targets) == 114, "wrong anchor-pair target count")
    for p in flat:
        require(
            sum(targets[pair] for pair in targets if p in pair) == 80,
            "anchor pair excess must be exhausted",
        )
        require(
            all(lower[pair] <= targets[pair] for pair in targets if p in pair),
            "pins contradict a forced anchor pair",
        )
    for a, h, link in zip(aset, hubs, links, strict=True):
        outside = Counter(p for b in link for p in set(b) - a)
        require(
            outside == {p: 2 if p == h else 1 for p in POINTS if p not in a},
            "pinned link violates the derived outside degrees",
        )

    hub_pairs = list(combinations(sorted(hubs), 2))
    graphs = [
        dict(zip(hub_pairs, values, strict=True))
        for values in product(range(3), repeat=6)
        if all(
            sum(c for pair, c in zip(hub_pairs, values, strict=True) if h in pair) == 2
            for h in hubs
        )
    ]
    require(len(graphs) == 6, "six hub graphs required")
    ordinary = [b for b in BLOCKS if all(len(set(b) & a) <= 1 for a in aset)]
    allowed = [b for b in BLOCKS if all(len(set(b) & a) != 2 for a in aset)]
    heavy = [b for b in allowed if any(a <= set(b) for a in aset)]
    require(
        (len(ordinary), len(allowed), len(heavy)) == (1200, 1476, 276), "universe count mismatch"
    )
    require(set(fixed) <= set(heavy), "pins violate allowed universe")
    barred = [b for b in BLOCKS if b not in fixed and b not in ordinary]
    for b in barred:
        require(
            any(
                sum(set(pair) <= set(f) for f in fixed) == 7
                for a in aset
                for pair in combinations(sorted(a), 2)
                if set(pair) <= set(b)
            ),
            "unexcluded nonordinary block",
        )

    capped = 0
    for triple in TRIPLES:
        if set(triple) in aset:
            continue
        if any(len(set(triple) & a) == 2 for a in aset):
            require(
                sum(set(triple) <= set(b) for b in fixed) in (1, 2),
                "pinned two-anchor triple cap fails",
            )
            require(
                not any(set(triple) <= set(b) for b in ordinary),
                "ordinary block adds to internal pair",
            )
        else:
            require(
                all(
                    any(
                        (targets | {pair: 5 + x for pair, x in graph.items()})[pair] == 5
                        for pair in combinations(triple, 2)
                    )
                    for graph in graphs
                ),
                "triple lacks a multiplicity-five pair",
            )
        capped += 1
    rows = [(ordinary, 36, 36)]
    supports = [(t, 1, INF if set(t) in aset else 2) for t in TRIPLES]
    supports += [((p,), 20, 20) for p in POINTS]
    supports += [
        (pair, targets[pair], targets[pair]) if pair in targets else (pair, 5, 7) for pair in PAIRS
    ]
    for support, lo, hi in supports:
        shift = sum(set(support) <= set(b) for b in fixed)
        rows.append(
            (
                [b for b in ordinary if set(support) <= set(b)],
                lo - shift,
                hi if hi == INF else hi - shift,
            )
        )
    receipt = {
        "anchors": anchors,
        "hubs": hubs,
        "pinned_blocks": fixed,
        "minimum_point_degrees": degree_lower,
        "own_pair_forced_duplicates": {
            f"{p},{h}": duplicate_receipts[tuple(sorted((p, h)))]
            for a, h in zip(anchors, hubs, strict=True)
            for p in a
        },
        "all_point_degrees_forced": 20,
        "ordinary_columns": len(ordinary),
        "barred_unpinned_columns": len(barred),
        "allowed_family_blocks": len(allowed),
        "heavy_family_columns": len(heavy),
        "hub_graphs": len(graphs),
        "hub_excess_vectors": [list(g.values()) for g in graphs],
        "forced_anchor_pair_equalities": len(targets),
        "nonanchor_triple_caps": capped,
    }
    return ordinary, rows, receipt


def check_model(proto, ordinary, rows):
    require(
        {f.name for f, _ in proto.ListFields()} == {"variables", "constraints"},
        "hidden top-level fields",
    )
    require(
        len(proto.variables) == 1200 and len(proto.constraints) == len(rows) == 697,
        "model shape mismatch",
    )
    for variable, block in zip(proto.variables, ordinary, strict=True):
        require(
            {f.name for f, _ in variable.ListFields()} == {"name", "domain"},
            "hidden variable fields",
        )
        require(
            variable.name == f"block_{BLOCKS.index(block)}" and list(variable.domain) == [0, 1],
            "variable order or domain mismatch",
        )
    index = {block: i for i, block in enumerate(ordinary)}
    for row, (support, lo, hi) in zip(proto.constraints, rows, strict=True):
        require({f.name for f, _ in row.ListFields()} == {"linear"}, "hidden constraint fields")
        require(list(row.linear.vars) == [index[b] for b in support], "support mismatch")
        require(list(row.linear.coeffs) == [1] * len(support), "coefficient mismatch")
        require(list(row.linear.domain) == [lo, hi], "bound mismatch")


def check_dual(certificate, ordinary, rows, manifest):
    require(
        set(certificate)
        == {
            "denominator",
            "weights",
            "rhs_numerator",
            "box_max_numerator",
            "gap",
            "proves_infeasible",
            "model_sha256",
            "heavy_sha256",
            "manifest_sha256",
        },
        "unexpected certificate fields",
    )
    for field in ("model_sha256", "heavy_sha256"):
        require(certificate[field] == manifest[field], "certificate binding mismatch")
    require(
        certificate["manifest_sha256"] == sha256(INPUT.read_bytes()).hexdigest(),
        "manifest binding mismatch",
    )
    scale = certificate["denominator"]
    require(type(scale) is int and scale > 0, "invalid certificate scale")
    require(
        type(certificate["weights"]) is list and certificate["weights"],
        "invalid certificate weights",
    )
    coefficients = dict.fromkeys(ordinary, 0)
    rhs, previous = 0, -1
    for term in certificate["weights"]:
        require(type(term) is list and len(term) == 2, "invalid certificate term")
        index, weight = term
        require(type(index) is int and type(weight) is int, "noninteger certificate term")
        require(previous < index < len(rows) and weight != 0, "bad certificate row")
        previous = index
        support, lo, hi = rows[index]
        require(weight > 0 or hi != INF, "infinite upper bound used")
        rhs += weight * (lo if weight > 0 else hi)
        for block in support:
            coefficients[block] += weight
    box = sum(max(0, value) for value in coefficients.values())
    gap = Fraction(rhs - box, scale)
    require(
        type(certificate["rhs_numerator"]) is int and certificate["rhs_numerator"] == rhs,
        "wrong certificate right side",
    )
    require(
        type(certificate["box_max_numerator"]) is int and certificate["box_max_numerator"] == box,
        "wrong certificate box bound",
    )
    require(certificate["gap"] == [gap.numerator, gap.denominator], "wrong exact gap")
    require(
        rhs > box and certificate["proves_infeasible"] is True,
        "certificate does not exclude feasibility",
    )
    return {
        "rhs_numerator": rhs,
        "box_max_numerator": box,
        "denominator": scale,
        "gap": [gap.numerator, gap.denominator],
        "signed_rows": len(certificate["weights"]),
    }


def main():
    manifest = json.loads(INPUT.read_text())
    anchors, hubs = [(1, 2, 3), (5, 6, 7), (9, 10, 11), (13, 14, 15)], [4, 8, 12, 16]
    fixed = list(map(tuple, manifest["heavy_blocks"]))
    ordinary, rows, receipt = derive(anchors, hubs, fixed)
    require(
        sha256(MODEL.read_bytes()).hexdigest() == manifest["model_sha256"], "model hash changed"
    )
    proto = text_format.Parse(MODEL.read_text(), cp_model_pb2.CpModelProto())
    check_model(proto, ordinary, rows)
    certificate = json.loads(DUAL.read_text())
    exact_certificate = check_dual(certificate, ordinary, rows, manifest)
    damaged = []
    hypotheses = []
    a = anchors.copy()
    a[1] = (1, 5, 6)
    hypotheses.append(("overlapping anchors", a, hubs, fixed))
    hypotheses.append(("repeated hub", anchors, [4, 4, 12, 16], fixed))
    hypotheses.append(("hub inside anchor", anchors, [1, 8, 12, 16], fixed))
    hypotheses.append(("missing pin", anchors, hubs, fixed[:-1]))
    hypotheses.append(("duplicate pin", anchors, hubs, fixed[:-1] + fixed[:1]))
    hypotheses.append(("malformed pin", anchors, hubs, [(0, 1, 2, 3, 4)] + fixed[1:]))
    hypotheses.append(("unsorted pin", anchors, hubs, [tuple(reversed(fixed[0]))] + fixed[1:]))
    f = fixed.copy()
    f[0] = (1, 2, 3, 5, 8)
    hypotheses.append(("own hub appears only once", anchors, hubs, f))
    for label, a, h, f in hypotheses:
        try:
            derive(a, h, f)
        except ValueError:
            damaged.append(label)
        else:
            raise AssertionError(f"damaged hypothesis accepted: {label}")
    for label in [
        "wrong triple bound",
        "wrong degree",
        "wrong pair",
        "wrong support",
        "wrong domain",
        "wrong order",
        "hidden enforcement",
        "hidden objective",
    ]:
        bad = deepcopy(proto)
        if label == "wrong triple bound":
            bad.constraints[2].linear.domain[1] += 1
        elif label == "wrong degree":
            bad.constraints[561].linear.domain[0] -= 1
        elif label == "wrong pair":
            bad.constraints[577].linear.domain[0] += 1
        elif label == "wrong support":
            next(r for r in bad.constraints[1:561] if r.linear.vars).linear.vars[0] += 1
        elif label == "wrong domain":
            bad.variables[0].domain[1] = 2
        elif label == "wrong order":
            bad.variables[0].name = "block_99999"
        elif label == "hidden enforcement":
            bad.constraints[0].enforcement_literal.append(0)
        else:
            bad.objective.vars.append(0)
            bad.objective.coeffs.append(1)
        try:
            check_model(bad, ordinary, rows)
        except ValueError:
            damaged.append(label)
        else:
            raise AssertionError(f"damaged model accepted: {label}")
    for field in [
        "denominator",
        "rhs_numerator",
        "box_max_numerator",
        "weights",
        "model_sha256",
        "heavy_sha256",
        "manifest_sha256",
        "gap",
        "proves_infeasible",
    ]:
        bad = deepcopy(certificate)
        if field in ("denominator", "rhs_numerator", "box_max_numerator"):
            bad[field] += 1
        elif field == "weights":
            bad[field][0][1] += 1
        elif field.endswith("sha256"):
            bad[field] = "0" * 64
        elif field == "gap":
            bad[field][0] += 1
        else:
            bad[field] = False
        try:
            check_dual(bad, ordinary, rows, manifest)
        except ValueError:
            damaged.append(f"certificate {field}")
        else:
            raise AssertionError(f"damaged certificate accepted: {field}")
    receipt |= {
        "passed": True,
        "rows_rebuilt": len(rows),
        "damaged_controls_rejected": damaged,
        "manifest_sha256": sha256(INPUT.read_bytes()).hexdigest(),
        "model_sha256": sha256(MODEL.read_bytes()).hexdigest(),
        "checker_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "exact_certificate": exact_certificate,
        "dual_sha256": sha256(DUAL.read_bytes()).hexdigest(),
        "scope": "Every 64-block cover containing these 28 pins obeys the audited LP. "
        "The short regularity theorem generalizes under the stated pin hypotheses. "
        "No unrestricted global exclusion is asserted.",
    }
    (HERE / "audit.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: receipt[k]
                for k in (
                    "passed",
                    "rows_rebuilt",
                    "ordinary_columns",
                    "hub_graphs",
                    "damaged_controls_rejected",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
