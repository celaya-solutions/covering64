# Document:    Independent Hub-Unrestricted Heavy Tuple Completion Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import argparse
import copy
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
WITNESS = HERE.parent / "four-seven-template-native-lookahead/performance-cycle-best.txt"


def geometry():
    blocks = [tuple(map(int, line.split())) for line in WITNESS.read_text().splitlines()]
    universe = list(itertools.combinations(range(1, 17), 5))
    assert len(blocks) == len(set(blocks)) == 64 and all(b in universe for b in blocks)
    assert set(Counter(p for b in blocks for p in b).values()) == {20}
    histogram = Counter(t for b in blocks for t in itertools.combinations(b, 3))
    assert 560 - len(histogram) == 10
    anchors = [set(range(start, start + 3)) for start in [1, 5, 9, 13]]
    heavy = [b for b in blocks if any(a <= set(b) for a in anchors)]
    assert len(heavy) == 28
    for anchor in anchors:
        local = [b for b in heavy if anchor <= set(b)]
        outside = Counter(p for b in local for p in set(b) - anchor)
        assert len(local) == 7 and outside == {
            p: 2 if p == max(anchor) + 1 else 1 for p in range(1, 17) if p not in anchor}
    ordinary = [b for b in universe if all(len(a & set(b)) <= 1 for a in anchors)]
    assert len(ordinary) == 1200
    return universe, ordinary, heavy


def inspect(proto):
    universe, ordinary, heavy = geometry()
    assert len(proto.variables) == 1200 and len(proto.constraints) == 577
    assert {field.name for field, _ in proto.ListFields()} <= {"variables", "constraints"}
    assert [v.name for v in proto.variables] == [f"block_{universe.index(b)}" for b in ordinary]
    assert all(list(v.domain) == [0, 1] for v in proto.variables)
    expected = [(list(range(1200)), [36, 36])]
    for t in itertools.combinations(range(1, 17), 3):
        fixed = sum(set(t) <= set(b) for b in heavy)
        ids = [i for i, b in enumerate(ordinary) if set(t) <= set(b)]
        expected.append((ids, [1 - fixed, 2**63 - 1]))
    for p in range(1, 17):
        fixed = sum(p in b for b in heavy)
        ids = [i for i, b in enumerate(ordinary) if p in b]
        expected.append((ids, [20 - fixed, 20 - fixed]))
    for row, (ids, domain) in zip(proto.constraints, expected, strict=True):
        assert row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
        assert list(row.linear.vars) == ids
        assert list(row.linear.coeffs) == [1] * len(ids)
        assert list(row.linear.domain) == domain


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    args = parser.parse_args()
    proto = text_format.Parse(args.model.read_text(), cp_model_pb2.CpModelProto())
    inspect(proto)
    mutations = []
    for index in [0, 12, 576]:
        damaged = copy.deepcopy(proto)
        damaged.constraints[index].linear.domain[0] += 1
        mutations.append(damaged)
    damaged = copy.deepcopy(proto)
    damaged.variables[0].domain[1] = 2
    mutations.append(damaged)
    damaged = copy.deepcopy(proto)
    damaged.solution_hint.vars.append(0)
    damaged.solution_hint.values.append(1)
    mutations.append(damaged)
    damaged = copy.deepcopy(proto)
    damaged.constraints.add().linear.domain.extend([0, 0])
    mutations.append(damaged)
    for damaged in mutations:
        try:
            inspect(damaged)
        except AssertionError:
            continue
        raise AssertionError("damaged heavy completion model accepted")
    report = {"passed": True, "variables": 1200, "constraints": 577,
              "fixed_heavy_blocks": 28, "damaged_controls_rejected": len(mutations),
              "model_sha256": hashlib.sha256(args.model.read_bytes()).hexdigest(),
              "witness_sha256": hashlib.sha256(WITNESS.read_bytes()).hexdigest(),
              "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "scope": "One fixed heavy tuple, degree20; no pair-count or hub-graph assumptions"}
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
