# Document:    Independent Parametric Heavy Cut Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import hashlib
import itertools as it
import json
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FAMILY = HERE.parent / "lookahead-parametric-cut"
DUAL = HERE.parent / "lookahead-heavy-strengthened/dual.json"
MODEL = ROOT / "experiments/scratch/lookahead-heavy-strengthened-v1.0.0/model.pbtxt"
WITNESS = HERE.parent / "four-seven-template-native-lookahead/performance-cycle-best.txt"


def rebuild():
    blocks = list(it.combinations(range(1, 17), 5))
    anchors = [set(range(a, a + 3)) for a in (1, 5, 9, 13)]
    hubs = {4, 8, 12, 16}
    ordinary = [b for b in blocks if all(len(set(b) & a) <= 1 for a in anchors)]
    heavy = [b for b in blocks if any(a <= set(b) for a in anchors)
             and all(len(set(b) & a) in (0, 1, 3) for a in anchors)]
    assert len(ordinary) == 1200 and len(heavy) == 276
    witness = [tuple(map(int, line.split())) for line in WITNESS.read_text().splitlines()]
    fixed = [b for b in witness if b in heavy]
    assert len(witness) == len(set(witness)) == 64 and len(fixed) == 28
    assert set(Counter(p for b in witness for p in b).values()) == {20}
    for anchor in anchors:
        local = [b for b in fixed if anchor <= set(b)]
        assert len(local) == 7
        assert Counter(p for b in local for p in set(b) - anchor) == {
            p: 2 if p == max(anchor) + 1 else 1 for p in range(1, 17) if p not in anchor}
    triples = list(it.combinations(range(1, 17), 3))
    pairs = list(it.combinations(range(1, 17), 2))
    targets = {}
    for a in anchors:
        for p in a:
            for q in range(1, 17):
                if p != q:
                    targets[tuple(sorted((p, q)))] = (
                        7 if q in a else 6 if q == max(a) + 1 else 5)
    hub_pairs = list(it.combinations(sorted(hubs), 2))
    graphs = [dict(zip(hub_pairs, counts)) for counts in it.product(range(3), repeat=6)
              if all(sum(c for pair, c in zip(hub_pairs, counts) if h in pair) == 2
                     for h in hubs)]
    assert len(graphs) == 6
    for triple in triples:
        if set(triple) in anchors:
            continue
        if any(len(set(triple) & a) == 2 for a in anchors):
            # Only that anchor's own blocks can cover this pair. Each outside
            # point occurs once, or twice for its hub, in its seven-block link.
            assert not any(set(triple) <= set(b) for b in ordinary)
        else:
            assert all(any((targets | {p: 5 + c for p, c in g.items()})[pair] == 5
                           for pair in it.combinations(triple, 2)) for g in graphs)
    # Row records: ordinary IDs, heavy IDs, unconditional lower/upper constants.
    rows = [(list(range(1200)), list(range(276)), 64, 64)]
    supports = [(t, 1, 2**63 - 1 if set(t) in anchors else 2) for t in triples]
    supports += [((p,), 20, 20) for p in range(1, 17)]
    supports += [(pair, targets[pair], targets[pair]) if pair in targets else (pair, 5, 7)
                 for pair in pairs]
    for support, lower, upper in supports:
        ids = [i for i, b in enumerate(ordinary) if set(support) <= set(b)]
        hids = [i for i, b in enumerate(heavy) if set(support) <= set(b)]
        rows.append((ids, hids, lower, upper))
    proto = text_format.Parse(MODEL.read_text(), cp_model_pb2.CpModelProto())
    assert len(proto.variables) == 1200 and len(proto.constraints) == 697 == len(rows)
    assert [v.name for v in proto.variables] == [f"block_{blocks.index(b)}" for b in ordinary]
    assert all(list(v.domain) == [0, 1] for v in proto.variables)
    assert {f.name for f, _ in proto.ListFields()} == {"variables", "constraints"}
    for row, (ids, hids, lower, upper) in zip(proto.constraints, rows, strict=True):
        shift = sum(heavy[i] in fixed for i in hids)
        expected_upper = upper if upper == 2**63 - 1 else upper - shift
        assert row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
        assert list(row.linear.vars) == ids and list(row.linear.coeffs) == [1] * len(ids)
        assert list(row.linear.domain) == [lower - shift, expected_upper]
    return blocks, ordinary, heavy, fixed, rows


def check(cut, basis, dual):
    blocks, ordinary, heavy, fixed, rows = basis
    assert dual["denominator"] == 1000
    ids = [i for i, _ in dual["weights"]]
    assert ids == sorted(set(ids)) and len(ids) == 531
    oc, hc, constant = [0] * 1200, [0] * 276, 0
    for i, weight in dual["weights"]:
        assert type(i) is int and 0 <= i < 697 and type(weight) is int and weight
        oi, hi, lower, upper = rows[i]
        bound = lower if weight > 0 else upper
        assert abs(bound) < 2**60
        constant += weight * bound
        for j in oi:
            oc[j] += weight
        for j in hi:
            hc[j] += weight
    box_max = sum(max(0, c) for c in oc)
    rhs = constant - box_max
    lhs = sum(c for b, c in zip(heavy, hc) if b in fixed)
    assert cut["direction"] == ">=" and cut["rhs"] == rhs
    assert cut["heavy_global_ids"] == [blocks.index(b) for b in heavy]
    assert cut["heavy_blocks"] == [list(b) for b in heavy]
    assert cut["ordinary_global_ids"] == [blocks.index(b) for b in ordinary]
    assert cut["coefficients"] == hc and cut["ordinary_combined_coefficients"] == oc
    assert cut["constant_numerator"] == constant
    assert cut["ordinary_box_max_numerator"] == box_max
    assert (rhs, lhs, rhs - lhs) == (108686, 98144, 10542)
    assert constant - lhs == dual["rhs_numerator"] == 10629
    assert box_max == dual["box_max_numerator"] == 87
    return rhs, lhs


def main():
    basis, dual = rebuild(), json.loads(DUAL.read_text())
    cut = json.loads((FAMILY / "cut.json").read_text())
    rhs, lhs = check(cut, basis, dual)
    controls = []
    for key in ["rhs", "constant_numerator", "ordinary_box_max_numerator"]:
        bad = copy.deepcopy(cut)
        bad[key] += 1
        controls.append(bad)
    for key in ["coefficients", "ordinary_combined_coefficients", "heavy_global_ids"]:
        bad = copy.deepcopy(cut)
        bad[key][0] += 1
        controls.append(bad)
    for bad in controls:
        try:
            check(bad, basis, dual)
        except AssertionError:
            continue
        raise AssertionError("damaged cut accepted")
    receipt = {"passed": True, "rhs": rhs, "fixed_tuple_lhs": lhs,
               "violation_numerator": rhs - lhs, "denominator": 1000,
               "heavy_columns": 276, "ordinary_columns": 1200, "reconstructed_rows": 697,
               "signed_rows": 531, "hub_graphs_retained": 6,
               "damaged_controls_rejected": len(controls),
               "scope": "Necessary for regular four-sevenfold template family only.",
               "sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in
                          {"checker": Path(__file__), "cut": FAMILY / "cut.json",
                           "dual": DUAL, "model": MODEL}.items()}}
    (HERE / "audit.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
