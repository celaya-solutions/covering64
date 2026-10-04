# Document:    Exact Binary Readback of Sole-Degree-Nineteen LP Primals
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      99ed5c8206de97011b7e66d4ea2d2ca837e9dcf45a0c60d36d0a6a89916954bf
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read every floating-point value exactly and recompute raw-protobuf residuals."""

import argparse
import copy
import gzip
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

TOLERANCE = Fraction(1, 10**7)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ratio(value):
    return [value.numerator, value.denominator]


def exact_residuals(model, values):
    require(len(values) == len(model.variables) == 4368, "wrong primal length")
    require(all(type(value) in (int, float) and math.isfinite(value) for value in values),
            "finite numeric values required")
    pairs = [float(value).as_integer_ratio() for value in values]
    denominator = max(divisor for _, divisor in pairs)
    require(all(denominator % divisor == 0 for _, divisor in pairs), "nonbinary denominator")
    integers = [numerator * (denominator // divisor) for numerator, divisor in pairs]
    domain = max(max(0, -value, value - denominator) for value in integers)
    row_error = 0
    worst_row = None
    for index, row in enumerate(model.constraints):
        require(row.WhichOneof("constraint") == "linear" and not row.enforcement_literal,
                "unconditional raw linear row required")
        require(len(row.linear.domain) == 2, "single interval required")
        total = sum(coefficient * integers[column]
                    for column, coefficient in zip(row.linear.vars, row.linear.coeffs, strict=True))
        lower, upper = row.linear.domain
        residual = max(0, lower * denominator - total, total - upper * denominator)
        if residual > row_error:
            row_error, worst_row = residual, index
    domain_error, constraint_error = Fraction(domain, denominator), Fraction(row_error, denominator)
    require(max(domain_error, constraint_error) <= TOLERANCE,
            "primal exceeds qualification tolerance")
    return {"domain_residual": ratio(domain_error), "row_residual": ratio(constraint_error),
            "maximum_domain_violation": float(domain_error),
            "maximum_row_violation": float(constraint_error), "worst_row_index": worst_row,
            "common_binary_denominator": denominator,
            "exact_feasible": domain == row_error == 0,
            "numerically_qualified": True,
            "exact_noninteger_variables": sum(value not in (0, denominator) for value in integers)}


def inventory(records, expected):
    require(len(records) == len(expected) == 38, "wrong result count")
    require({record["id"] for record in records} == set(expected), "missing or duplicate case")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.directory / "input/manifest.json").read_text())
    expected = {row["id"]: row for row in manifest["cases"]}
    records_path = args.directory / "results.json.gz"
    records = json.loads(gzip.decompress(records_path.read_bytes()))
    inventory(records, expected)
    checked = []
    first = None
    for record in records:
        entry = expected[record["id"]]
        path = args.directory / "input" / f"{record['id']}.pbtxt"
        require(sha(path) == entry["model_sha256"] == record["model_sha256"], "model hash mismatch")
        model = text_format.Parse(path.read_text(), cp_model_pb2.CpModelProto())
        primal_path = args.directory / record["id"] / "primal.json.gz"
        require(sha(primal_path) == record["primal_sha256"], "primal hash mismatch")
        primal = json.loads(gzip.decompress(primal_path.read_bytes()))
        require(primal["id"] == record["id"], "primal identity mismatch")
        result = exact_residuals(model, primal["values"])
        require(result["exact_noninteger_variables"] > 0 and not record["candidate_extracted"]
                and not record["cover_found"] and not record["proves_infeasible"],
                "outcome claim does not match fractional readback")
        checked.append({"id": record["id"], "model_sha256": sha(path),
                        "primal_sha256": sha(primal_path), **result})
        if first is None:
            first = model, primal["values"]
    damaged = []
    model, values = first
    fixed_index = next(row.linear.vars[0] for row in model.constraints
                       if len(row.linear.vars) == 1 and list(row.linear.domain) == [1, 1])
    mutations = [
        ("missing value", lambda data: data.pop()),
        ("NaN value", lambda data: data.__setitem__(0, float("nan"))),
        ("infinite value", lambda data: data.__setitem__(0, float("inf"))),
        ("Boolean value", lambda data: data.__setitem__(0, True)),
        ("negative domain", lambda data: data.__setitem__(0, -0.01)),
        ("upper domain", lambda data: data.__setitem__(0, 1.01)),
        ("broken fixed block", lambda data: data.__setitem__(fixed_index, 0.99)),
    ]
    for name, mutation in mutations:
        data = list(values)
        mutation(data)
        try:
            exact_residuals(model, data)
        except ValueError:
            damaged.append(name)
        else:
            raise ValueError(f"damaged primal accepted: {name}")
    for name, mutation in (("missing case", lambda data: data.pop()),
                           ("duplicate case", lambda data: data.__setitem__(0, data[1]))):
        data = copy.deepcopy(records)
        mutation(data)
        try:
            inventory(data, expected)
        except ValueError:
            damaged.append(name)
        else:
            raise ValueError(f"damaged result inventory accepted: {name}")
    result = {"checker_sha256": sha(Path(__file__)), "results_sha256": sha(records_path),
              "cases": checked, "damaged_controls_rejected": damaged,
              "maximum_row_violation": max(row["maximum_row_violation"] for row in checked),
              "maximum_domain_violation": max(row["maximum_domain_violation"] for row in checked),
              "exact_feasible_vectors": sum(row["exact_feasible"] for row in checked),
              "scope": "Exact arithmetic on saved IEEE754 binary values confirms residuals "
                       "within1e-7. Nonzero residuals remain numerical feasibility only; "
                       "fractional vectors are not integer covering witnesses."}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "cases"}, indent=2))


if __name__ == "__main__":
    main()
