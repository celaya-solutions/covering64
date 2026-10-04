# Document:    Independent Strong Heavy Completion Encoding and Preservation Audit
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
import itertools
import json
from pathlib import Path

from check import geometry, inspect
from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODEL = ROOT / "experiments/scratch/lookahead-heavy-strengthened-v1.0.0/model.pbtxt"


def validate(proto):
    _, ordinary, heavy = geometry()
    groups = [set(range(start, start + 3)) for start in [1, 5, 9, 13]]
    heavy_triples = {tuple(sorted(g)) for g in groups}
    hubs = [4, 8, 12, 16]
    pairs = list(itertools.combinations(range(1, 17), 2))
    triples = list(itertools.combinations(range(1, 17), 3))
    assert len(proto.constraints) == 697
    restored = copy.deepcopy(proto)
    del restored.constraints[577:]
    for row in restored.constraints[1:561]:
        row.linear.domain[1] = 2**63 - 1
    inspect(restored)
    target = {}
    for group in groups:
        for p in group:
            lower_sum = 0
            for q in range(1, 17):
                if q == p:
                    continue
                value = 7 if q in group else 6 if q == max(group) + 1 else 5
                target[tuple(sorted((p, q)))] = value
                lower_sum += value
            assert lower_sum == 80
    assert len(target) == 114
    hub_pairs = list(itertools.combinations(hubs, 2))
    graphs = []
    for excess in itertools.product(range(3), repeat=6):
        if all(sum(x for pair, x in zip(hub_pairs, excess, strict=True) if p in pair) == 2
               for p in hubs):
            graphs.append({pair: 5 + x for pair, x in zip(hub_pairs, excess, strict=True)})
    assert len(graphs) == 6
    assert sorted(sorted(g.values()) for g in graphs) == sorted(
        [[5, 5, 6, 6, 6, 6]] * 3 + [[5, 5, 5, 5, 7, 7]] * 3)
    for i, triple in enumerate(triples):
        fixed = sum(set(triple) <= set(block) for block in heavy)
        if triple in heavy_triples:
            assert proto.constraints[1 + i].linear.domain[1] == 2**63 - 1
            continue
        assert proto.constraints[1 + i].linear.domain[1] == 2 - fixed
        for graph in graphs:
            full_pairs = target | graph
            if min(full_pairs[p] for p in itertools.combinations(triple, 2)) > 5:
                # Own-anchor/hub triples are fixed by the seven-block template.
                assert fixed <= 2 and not any(set(triple) <= set(b) for b in ordinary)
    for row, pair in zip(proto.constraints[577:], pairs, strict=True):
        fixed = sum(set(pair) <= set(b) for b in heavy)
        lower, upper = (target[pair], target[pair]) if pair in target else (5, 7)
        ids = [i for i, b in enumerate(ordinary) if set(pair) <= set(b)]
        assert row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
        assert list(row.linear.vars) == ids and list(row.linear.coeffs) == [1] * len(ids)
        assert list(row.linear.domain) == [lower - fixed, upper - fixed]


def main():
    proto = text_format.Parse(MODEL.read_text(), cp_model_pb2.CpModelProto())
    validate(proto)
    mutations = []
    for index, endpoint in [(2, 1), (577, 0), (696, 1)]:
        damaged = copy.deepcopy(proto)
        damaged.constraints[index].linear.domain[endpoint] += 1
        mutations.append(damaged)
    damaged = copy.deepcopy(proto)
    damaged.constraints[600].enforcement_literal.append(0)
    mutations.append(damaged)
    for damaged in mutations:
        try:
            validate(damaged)
        except AssertionError:
            continue
        raise AssertionError("damaged strengthened model accepted")
    report = {"passed": True, "variables": 1200, "constraints": 697,
              "anchor_pair_equalities": 114, "hub_pair_bounds": 6, "hub_graphs": 6,
              "nonheavy_triple_caps": 556, "damaged_controls_rejected": len(mutations),
              "model_sha256": hashlib.sha256(MODEL.read_bytes()).hexdigest(),
              "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "base_checker_sha256": hashlib.sha256((HERE / "check.py").read_bytes()).hexdigest(),
              "scope": "Necessary strengthening for this regular four-sevenfold heavy tuple; "
                       "all six hub graphs permitted"}
    (HERE / "strengthened-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
