# Document:    Independent Dual Replay for the Cut-Guided Heavy Tuple
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import hashlib
import json
from fractions import Fraction
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODEL = ROOT / "experiments/scratch/cut-pilot-heavy-completion-v1.0.0/model.pbtxt"
DUAL = HERE.parent / "cut-pilot-heavy-completion/dual.json"


def check(proto, dual):
    denominator = dual["denominator"]
    assert type(denominator) is int and denominator > 0
    weights = dual["weights"]
    assert weights and all(len(entry) == 2 for entry in weights)
    ids = [i for i, _ in weights]
    assert ids == sorted(set(ids))
    columns, rhs = [0] * len(proto.variables), 0
    for i, weight in weights:
        assert type(i) is int and 0 <= i < len(proto.constraints)
        assert type(weight) is int and weight != 0
        row = proto.constraints[i]
        assert row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
        assert len(row.linear.domain) == 2
        bound = row.linear.domain[0 if weight > 0 else 1]
        assert abs(bound) < 2**60
        rhs += weight * bound
        for variable, coefficient in zip(row.linear.vars, row.linear.coeffs, strict=True):
            assert 0 <= variable < len(columns)
            columns[variable] += weight * coefficient
    assert all(list(v.domain) == [0, 1] for v in proto.variables)
    maximum = sum(max(0, value) for value in columns)
    gap = Fraction(rhs - maximum, denominator)
    assert rhs == dual["rhs_numerator"] and maximum == dual["box_max_numerator"]
    assert [gap.numerator, gap.denominator] == dual["gap"]
    assert gap > 0 and dual["proves_infeasible"] is True
    return rhs, maximum, gap


def main():
    model_bytes, dual_bytes = MODEL.read_bytes(), DUAL.read_bytes()
    gate = json.loads((HERE / "gate.json").read_text())
    assert gate["passed"] and gate["model_sha256"] == hashlib.sha256(model_bytes).hexdigest()
    assert gate["checker_sha256"] == hashlib.sha256((HERE / "check.py").read_bytes()).hexdigest()
    proto = text_format.Parse(model_bytes.decode(), cp_model_pb2.CpModelProto())
    dual = json.loads(dual_bytes)
    rhs, maximum, gap = check(proto, dual)
    cases = []
    for key in ["denominator", "rhs_numerator", "box_max_numerator"]:
        damaged = copy.deepcopy(dual)
        damaged[key] += 1
        cases.append(damaged)
    damaged = copy.deepcopy(dual)
    damaged["weights"][0][1] += 1
    cases.append(damaged)
    damaged = copy.deepcopy(dual)
    damaged["weights"].insert(0, damaged["weights"][0])
    cases.append(damaged)
    for damaged in cases:
        try:
            check(proto, damaged)
        except AssertionError:
            continue
        raise AssertionError("damaged certificate accepted")
    result = {"passed": True, "model_sha256": hashlib.sha256(model_bytes).hexdigest(),
              "dual_sha256": hashlib.sha256(dual_bytes).hexdigest(),
              "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "signed_rows": len(dual["weights"]), "ordinary_columns": len(proto.variables),
              "rhs_numerator": rhs, "box_max_numerator": maximum,
              "denominator": dual["denominator"], "gap": [gap.numerator, gap.denominator],
              "damaged_certificates_rejected": len(cases),
              "scope": "Fixed28-heavy-block tuple only, in the regular four-sevenfold family; "
                       "all six hub graphs retained. No whole first-link or global exclusion."}
    (HERE / "dual-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
