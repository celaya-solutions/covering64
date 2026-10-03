# Document:    Independent Fixed Heavy-Link LP Certificate Checker
# Version:     v1.0.2
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      466c2dcce6a27e8fdab64bfedf264b77987fa1027c0d8942f5d97ba0056f255e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Exact certificate audit from archived protobuf and rows; no solver or builder calls."""

import argparse
import gzip
import hashlib
import json
from fractions import Fraction
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value):
    return type(value) is int


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_rows(rows, width):
    require(integer(width) and width > 0, "bad width")
    for row in rows:
        require(isinstance(row, (tuple, list)) and len(row) == 4, "bad row shape")
        ids, coefficients, lo, hi = row
        require(len(ids) == len(coefficients), "coefficient count mismatch")
        require(all(integer(i) and 0 <= i < width for i in ids), "bad column index")
        require(len(set(ids)) == len(ids), "duplicate column index")
        require(all(integer(c) for c in coefficients), "noninteger coefficient")
        require(all(v is None or integer(v) for v in (lo, hi)), "noninteger bound")
        require(lo is None or hi is None or lo <= hi, "reversed row interval")


def check_certificate(rows, width, certificate):
    checked_rows(rows, width)
    denominator = certificate["denominator"]
    require(integer(denominator) and denominator > 0, "bad denominator")
    require(all(integer(certificate[k]) for k in
                ["rhs_numerator", "box_max_numerator", "checked_columns"]), "noninteger claim")
    claimed_gap = certificate["gap"]
    require(isinstance(claimed_gap, list) and len(claimed_gap) == 2 and
            all(integer(v) for v in claimed_gap) and claimed_gap[1] > 0, "malformed gap")
    multipliers = {}
    for item in certificate["weights"]:
        require(isinstance(item, (tuple, list)) and len(item) == 2, "bad multiplier entry")
        index, value = item
        require(integer(index) and 0 <= index < len(rows), "bad row index")
        require(index not in multipliers, "duplicate multiplier row")
        require(integer(value) and value != 0, "bad integer multiplier")
        multipliers[index] = value
    coefficients = [0] * width
    lower_sum = 0
    for index, weight in multipliers.items():
        ids, values, lo, hi = rows[index]
        if weight > 0:
            require(lo is not None, "positive weight on missing lower bound")
            lower_sum += weight * lo
        else:
            require(hi is not None, "negative weight on missing upper bound")
            lower_sum += weight * hi
        for column, coefficient in zip(ids, values, strict=True):
            coefficients[column] += weight * coefficient
    # Choose x_j=1 exactly where the coefficient is positive to maximize over [0,1]^n.
    box_bound = sum(c for c in coefficients if c > 0)
    gap = Fraction(lower_sum - box_bound, denominator)
    require(certificate["rhs_numerator"] == lower_sum, "damaged weighted bound")
    require(certificate["box_max_numerator"] == box_bound, "damaged box bound")
    require(certificate["gap"] == [gap.numerator, gap.denominator], "damaged gap")
    require(certificate["checked_columns"] == width, "damaged column count")
    require(type(certificate["proves_infeasible"]) is bool, "nonboolean claim")
    require(certificate["proves_infeasible"] == (gap > 0), "damaged exclusion claim")
    return {"gap": [gap.numerator, gap.denominator], "proves_infeasible": gap > 0,
            "rows": len(rows), "columns": width, "nonzero_weights": len(multipliers)}


def proto_rows(path):
    proto = cp_model_pb2.CpModelProto()
    text_format.Parse(path.read_text(), proto)
    require(all(list(v.domain) == [0, 1] for v in proto.variables), "non-unit-box variable")
    rows = []
    for constraint in proto.constraints:
        require(not constraint.enforcement_literal, "conditional row")
        require(constraint.WhichOneof("constraint") == "linear", "nonlinear row")
        row = constraint.linear
        require(len(row.domain) == 2, "non-interval linear domain")
        lo, hi = row.domain
        rows.append([list(row.vars), list(row.coeffs),
                     None if lo == -(1 << 63) else lo,
                     None if hi == (1 << 63) - 1 else hi])
    checked_rows(rows, len(proto.variables))
    return proto, rows


def audit_run(folder):
    metadata = json.loads((folder / "metadata.json").read_text())
    representatives = folder / "representatives.json"
    require(sha(representatives) == metadata["representatives_sha256"], "representatives hash")
    payload = json.loads(representatives.read_text())
    representatives_by_case = {}
    for group in payload["cases"]:
        case = group["case"]
        require(case in {"cycle", "matching"} and case not in representatives_by_case,
                "bad or duplicate case")
        entries = {rep["id"]: rep for rep in group["representatives"]}
        require(len(entries) == len(group["representatives"]), "duplicate representative id")
        representatives_by_case[case] = entries
    for name, digest in metadata["sources"].items():
        require(sha(folder / name) == digest, "source archive hash")
    full_blocks = list(combinations(range(1, 17), 5))
    block_ids = {b: i for i, b in enumerate(full_blocks)}
    models = {}
    for case, digests in metadata["models"].items():
        model_path, rows_path = folder / f"{case}-base.pbtxt", folder / f"{case}-rows.json.gz"
        require(sha(model_path) == digests["model_sha256"], "raw model hash")
        require(sha(rows_path) == digests["rows_sha256"], "raw rows hash")
        proto, rows = proto_rows(model_path)
        archived = json.loads(gzip.decompress(rows_path.read_bytes()))
        require(archived == {"width": len(proto.variables), "rows": rows}, "rows differ from proto")
        require(all(proto.variables[i].name == f"block_{i}" for i in range(len(full_blocks))),
                "block variable ordering")
        models[case] = (rows, len(proto.variables))
    results = json.loads(gzip.decompress((folder / "results.json.gz").read_bytes()))
    seen, checks = set(), []
    for result in results:
        key = result["case"], result["id"]
        require(key not in seen, "duplicate result")
        seen.add(key)
        rep = representatives_by_case[key[0]][key[1]]
        edges = rep["edges"]
        require(len(edges) == 7 and len({tuple(e) for e in edges}) == 7, "bad edge count")
        require(all(len(e) == 2 and all(integer(p) and 4 <= p <= 16 for p in e)
                    and e[0] < e[1] for e in edges), "bad edge labels")
        fixed = [block_ids[(1, 2, 3, *edge)] for edge in edges]
        require(result["fixed_ids"] == fixed, "fixed IDs differ from representative")
        base, width = models[key[0]]
        rows = base + [[[i], [1], 1, 1] for i in fixed]
        require(result["checked_rows"] == len(rows), "row count mismatch")
        require(result["checked_columns"] == width, "column count mismatch")
        certificate = result.get("certificate")
        if certificate is None:
            require(result["proves_infeasible"] is False, "unsupported exclusion")
            checked = {"proves_infeasible": False, "certificate": None}
        else:
            checked = check_certificate(rows, width, certificate)
            require(result["proves_infeasible"] == checked["proves_infeasible"],
                    "result and certificate differ")
        checks.append({"case": key[0], "id": key[1], **checked})
    require(metadata["case"] in {"cycle", "matching", "both"}, "bad selected case")
    limit = metadata["limit"]
    require(limit is None or integer(limit) and limit > 0, "bad selected limit")
    expected = {(group["case"], rep["id"]) for group in payload["cases"]
                if metadata["case"] in (group["case"], "both")
                for rep in group["representatives"][:limit]}
    require(seen == expected, "incomplete or unexpected representative coverage")
    return {"scope": "Only the archived fixed-link branches; no cover or global bound claim.",
            "checker_sha256": sha(Path(__file__)), "metadata_sha256": sha(folder / "metadata.json"),
            "results_sha256": sha(folder / "results.json.gz"), "records": len(checks),
            "expected_records": len(expected), "complete_selected_coverage": True,
            "excluded": sum(c["proves_infeasible"] for c in checks), "checks": checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), "refusing to overwrite audit")
    result = audit_run(args.run)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["records", "excluded"]}))


if __name__ == "__main__":
    main()
