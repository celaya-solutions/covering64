# Document:    Independent Aggregated Circle Incidence Model Audit
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


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(proto, pool, lines, circles):
    universe = list(itertools.combinations(range(1, 17), 5))
    assert len(pool) == 288 and pool == sorted(set(pool))
    assert len(proto.variables) == 288 and len(proto.constraints) == 69
    assert {d.name for d, _ in proto.ListFields()} <= {"variables", "constraints"}
    for variable, block in zip(proto.variables, pool, strict=True):
        assert variable.name == f"block_{universe.index(block)}"
        assert list(variable.domain) == [0, 1]
    expected = [({i: 1 for i in range(288)}, [64, 64])]
    for line in lines:
        triples = list(itertools.combinations(line, 3))
        supports = [{i: 1 for i, b in enumerate(pool) if set(t) <= set(b)} for t in triples]
        assert len(supports[0]) == 12 and all(s == supports[0] for s in supports)
        expected.append((supports[0], [1, 2**63 - 1]))
    for circle in circles:
        triples = list(itertools.combinations(circle, 3))
        coefficients = {i: sum(set(t) <= set(b) for t in triples)
                        for i, b in enumerate(pool)}
        coefficients = {i: v for i, v in coefficients.items() if v}
        assert sorted(coefficients.values()) == [1] * 30 + [10]
        expected.append((coefficients, [10, 2**63 - 1]))
    for row, (coefficients, domain) in zip(proto.constraints, expected, strict=True):
        assert row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
        assert list(row.linear.vars) == sorted(coefficients)
        assert list(row.linear.coeffs) == [coefficients[i] for i in sorted(coefficients)]
        assert list(row.linear.domain) == domain


def main():
    manifest = json.loads((HERE / "manifest.json").read_text())
    reference_path = HERE.parent / "affine-extension-independent/pool.json"
    reference = json.loads(reference_path.read_text())
    model_path = ROOT / manifest["model"]
    assert digest(model_path) == manifest["model_sha256"]
    assert digest(reference_path) == manifest["source_pool_sha256"]
    pool = list(map(tuple, reference["pool"]))
    lines, circles = list(map(tuple, reference["lines"])), list(map(tuple, reference["circles"]))
    proto = text_format.Parse(model_path.read_text(), cp_model_pb2.CpModelProto())
    inspect(proto, pool, lines, circles)
    mutations = []
    damaged = copy.deepcopy(proto)
    del damaged.variables[-1]
    mutations.append(damaged)
    damaged = copy.deepcopy(proto)
    damaged.variables[0].domain[1] = 2
    mutations.append(damaged)
    damaged = copy.deepcopy(proto)
    damaged.constraints[0].linear.domain[0] = 63
    mutations.append(damaged)
    damaged = copy.deepcopy(proto)
    damaged.constraints[21].linear.coeffs[0] += 1
    mutations.append(damaged)
    damaged = copy.deepcopy(proto)
    damaged.constraints[21].linear.domain[0] = 9
    mutations.append(damaged)
    damaged = copy.deepcopy(proto)
    damaged.constraints[1].enforcement_literal.append(0)
    mutations.append(damaged)
    damaged = copy.deepcopy(proto)
    damaged.solution_hint.vars.append(0)
    damaged.solution_hint.values.append(1)
    mutations.append(damaged)
    for damaged in mutations:
        try:
            inspect(damaged, pool, lines, circles)
        except AssertionError:
            continue
        raise AssertionError("damaged aggregate model accepted")
    report = {"passed": True, "variables": 288, "constraints": 69,
              "damaged_controls_rejected": len(mutations),
              "model_sha256": digest(model_path), "checker_sha256": digest(Path(__file__)),
              "pool_sha256": digest(reference_path),
              "method": "Each circle row independently sums its ten original triple-coverage rows",
              "scope": "Necessary relaxation of the fixed 288-block pool only"}
    (HERE / "independent-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
