# Document:    Independent Joint Partial-Core Model Audit
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

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODEL = ROOT / "experiments/scratch/partial-core-holes-v1.0.0/model.pbtxt"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
TRIPLES = list(itertools.combinations(range(1, 17), 3))


def read_blocks(path, size):
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) == size
    assert all(block in BLOCKS for block in blocks)
    return set(blocks)


def inspect(proto, core, hint):
    assert {field.name for field, _ in proto.ListFields()} == {
        "variables", "constraints", "objective", "solution_hint"}
    assert len(proto.variables) == 4928 and len(proto.constraints) == 1122
    assert [v.name for v in proto.variables] == (
        [f"block_{i}" for i in range(4368)] + [f"missing_{i}" for i in range(560)])
    assert all(list(v.domain) == [0, 1] for v in proto.variables)
    expected = [(list(range(4368)), [64, 64], []),
                ([i for i, b in enumerate(BLOCKS) if b in core], [52, 55], [])]
    for tid, triple in enumerate(TRIPLES):
        ids = [i for i, b in enumerate(BLOCKS) if set(triple) <= set(b)]
        assert len(ids) == 78
        expected.extend([(ids, [0, 0], [4368 + tid]),
                         (ids, [1, 2**63 - 1], [-4369 - tid])])
    for row, (ids, domain, literals) in zip(proto.constraints, expected, strict=True):
        assert {field.name for field, _ in row.ListFields()} <= {
            "linear", "enforcement_literal"}
        assert row.WhichOneof("constraint") == "linear"
        assert list(row.linear.vars) == ids
        assert list(row.linear.coeffs) == [1] * len(ids)
        assert list(row.linear.domain) == domain
        assert list(row.enforcement_literal) == literals
    objective = proto.objective
    assert list(objective.vars) == list(range(4368, 4928))
    assert list(objective.coeffs) == [1] * 560
    assert objective.offset == 0 and objective.scaling_factor == 1
    assert {field.name for field, _ in objective.ListFields()} <= {
        "vars", "coeffs", "offset", "scaling_factor"}
    covered = {t for block in hint for t in itertools.combinations(block, 3)}
    values = [int(b in hint) for b in BLOCKS] + [int(t not in covered) for t in TRIPLES]
    assert list(proto.solution_hint.vars) == list(range(4928))
    assert list(proto.solution_hint.values) == values
    assert len(hint & core) == 55 and 560 - len(covered) == 11
    for row in proto.constraints:
        literals = row.enforcement_literal
        if literals and any(values[lit] == 0 if lit >= 0 else values[-lit - 1] == 1
                            for lit in literals):
            continue
        total = sum(values[i] * c for i, c in zip(row.linear.vars, row.linear.coeffs))
        assert row.linear.domain[0] <= total <= row.linear.domain[1]


def main():
    core, hint = read_blocks(HERE / "core.txt", 60), read_blocks(HERE / "hint.txt", 64)
    metadata = json.loads((HERE / "metadata.json").read_text())
    assert hashlib.sha256(MODEL.read_bytes()).hexdigest() == metadata["model_sha256"]
    assert hashlib.sha256((HERE / "core.txt").read_bytes()).hexdigest() == (
        "7011e57be2714b1e1a16d4419ecb55a0160e25806f5db5dd786891aa17d0a5db")
    proto = text_format.Parse(MODEL.read_text(), cp_model_pb2.CpModelProto())
    inspect(proto, core, hint)
    damaged = []
    for kind in range(7):
        bad = copy.deepcopy(proto)
        if kind == 0:
            bad.constraints[0].linear.domain[0] = 63
        elif kind == 1:
            bad.constraints[1].linear.domain[1] = 56
        elif kind == 2:
            bad.constraints[2].linear.vars[0] += 1
        elif kind == 3:
            bad.constraints[3].enforcement_literal[0] += 1
        elif kind == 4:
            bad.objective.coeffs[0] = 0
        elif kind == 5:
            bad.solution_hint.values[0] = 1 - bad.solution_hint.values[0]
        else:
            bad.constraints.add().CopyFrom(proto.constraints[0])
        try:
            inspect(bad, core, hint)
        except AssertionError:
            damaged.append(kind)
            continue
        raise AssertionError("damaged model accepted")
    result = {"passed": True, "model_sha256": metadata["model_sha256"],
              "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "all_block_columns": 4368, "exact_hole_indicators": 560,
              "reconstructed_rows": 1122, "damaged_models_rejected": len(damaged),
              "complete_feasible_hint": True, "hint_holes": 11,
              "scope": "Only original-core overlap 52..55; no degree or hole ceiling."}
    (HERE / "gate.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
