# Document:    Independent Exact Dual Replay for the Ten-Hole Heavy Tuple
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
import json
from fractions import Fraction
from pathlib import Path

from check_strengthened import MODEL, validate
from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
DUAL = HERE.parent / "lookahead-heavy-strengthened/dual.json"


def check(proto, certificate):
    denominator = certificate["denominator"]
    assert type(denominator) is int and denominator > 0
    weights = certificate["weights"]
    assert weights and all(len(item) == 2 for item in weights)
    ids = [i for i, _ in weights]
    assert ids == sorted(set(ids))
    columns = [0] * len(proto.variables)
    rhs = 0
    for i, weight in weights:
        assert type(i) is int and 0 <= i < len(proto.constraints)
        assert type(weight) is int and weight
        row = proto.constraints[i]
        assert row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
        assert len(row.linear.domain) == 2
        bound = row.linear.domain[0 if weight > 0 else 1]
        assert -(2**60) < bound < 2**60
        rhs += weight * bound
        for j, coefficient in zip(row.linear.vars, row.linear.coeffs, strict=True):
            columns[j] += weight * coefficient
    assert all(list(v.domain) == [0, 1] for v in proto.variables)
    box_max = sum(max(0, coefficient) for coefficient in columns)
    gap = Fraction(rhs - box_max, denominator)
    assert rhs == certificate["rhs_numerator"]
    assert box_max == certificate["box_max_numerator"]
    assert certificate["gap"] == [gap.numerator, gap.denominator]
    assert gap > 0 and certificate["proves_infeasible"] is True
    return rhs, box_max, gap


def main():
    proto = text_format.Parse(MODEL.read_text(), cp_model_pb2.CpModelProto())
    validate(proto)
    certificate = json.loads(DUAL.read_text())
    rhs, box_max, gap = check(proto, certificate)
    damaged = []
    for field in ["rhs_numerator", "box_max_numerator", "denominator"]:
        d = copy.deepcopy(certificate)
        d[field] += 1
        damaged.append(d)
    d = copy.deepcopy(certificate)
    d["weights"][0][1] += 1
    damaged.append(d)
    d = copy.deepcopy(certificate)
    d["weights"].insert(1, d["weights"][0])
    damaged.append(d)
    for d in damaged:
        try:
            check(proto, d)
        except AssertionError:
            continue
        raise AssertionError("damaged dual accepted")
    result = {"passed": True, "model_sha256": hashlib.sha256(MODEL.read_bytes()).hexdigest(),
              "dual_sha256": hashlib.sha256(DUAL.read_bytes()).hexdigest(),
              "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "signed_rows": len(certificate["weights"]), "ordinary_columns": 1200,
              "rhs_numerator": rhs, "box_max_numerator": box_max,
              "denominator": certificate["denominator"], "gap": [gap.numerator, gap.denominator],
              "damaged_controls_rejected": len(damaged),
              "scope": "Only this fixed heavy tuple in the regular four-sevenfold family; "
                       "all hub graphs allowed. No first-link or global exclusion."}
    (HERE / "dual-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
