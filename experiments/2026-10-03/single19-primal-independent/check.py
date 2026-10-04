# Document:    Independent Sole Degree Nineteen Primal Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Recount all raw rows using one exact common binary denominator per saved vector."""

import copy
import gzip
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/single19-lp-v1.0.0"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return (
        json.loads(gzip.decompress(path.read_bytes()))
        if path.suffix == ".gz"
        else (json.loads(path.read_text()))
    )


def check_vector(primal, record, rows):
    require(primal["id"] == record["id"], "wrong primal ID")
    values = primal["values"]
    require(
        len(values) == 4368
        and all(type(value) in (int, float) and math.isfinite(value) for value in values),
        "malformed primal vector",
    )
    ratios = [float(value).as_integer_ratio() for value in values]
    denominator = max(den for _, den in ratios)
    require(all(denominator % den == 0 for _, den in ratios), "nonbinary floating value")
    integers = [num * (denominator // den) for num, den in ratios]
    row_residual = 0
    for ids, coefficients, lower, upper in rows:
        require(
            len(ids) == len(coefficients)
            and len(ids) == len(set(ids))
            and all(type(i) is int and 0 <= i < 4368 for i in ids)
            and all(type(c) is int for c in coefficients),
            "malformed row",
        )
        dot = sum(integers[i] * coefficient for i, coefficient in zip(ids, coefficients))
        if lower is not None:
            row_residual = max(row_residual, lower * denominator - dot)
        if upper is not None:
            row_residual = max(row_residual, dot - upper * denominator)
    domain_residual = max(0, -min(integers), max(integers) - denominator)
    require(
        Fraction(row_residual, denominator) <= Fraction(1, 10000000)
        and Fraction(domain_residual, denominator) <= Fraction(1, 10000000),
        "saved vector violates numerical qualification tolerance",
    )
    fractional = sum(1e-7 < value < 1 - 1e-7 for value in values)
    require(
        fractional == record["primal_metrics"]["fractional_variables"] and fractional > 0,
        "wrong fractionality claim",
    )
    require(
        record["feasibility_lp"]["status"] == "OPTIMAL"
        and record["proves_infeasible"] is False
        and record["cover_found"] is False
        and record["candidate_extracted"] is False,
        "unsupported result claim",
    )
    exact_row = Fraction(row_residual, denominator)
    exact_domain = Fraction(domain_residual, denominator)
    return {
        "fractional_variables": fractional,
        "exact_row_residual": [exact_row.numerator, exact_row.denominator],
        "exact_domain_residual": [exact_domain.numerator, exact_domain.denominator],
        "exactly_rational_feasible": row_residual == domain_residual == 0,
    }


def main():
    metadata = read(RAW / "metadata.json")
    results = read(RAW / "results.json.gz")
    require(
        sha(RAW / "metadata.json")
        == "89ba9b4a3c062f59d0a3a60adb53fbf102b7909113238f055981c744bced5463",
        "frozen metadata changed",
    )
    require(
        sha(RAW / "results.json.gz")
        == "89204d6e6991ffed6032aa7440d76d3c3a65cca7d1717ba66ee60b654b571e6f",
        "frozen results changed",
    )
    for name, digest in metadata["sources"].items():
        require(sha(RAW / name) == digest, "source snapshot changed")
    audit_path = HERE.parent / "single19-independent/model-audit.json"
    audit = read(audit_path)
    require(sha(audit_path) == metadata["model_audit_sha256"], "model audit changed")
    require(
        sha(RAW / "input/manifest.json")
        == metadata["input_manifest_sha256"]
        == audit["input_manifest_sha256"],
        "model manifest hash mismatch",
    )
    model_audits = {item["id"]: item for item in audit["cases"]}
    roadmap = read(HERE.parent / "degree19-roadmap-independent/audit.json")
    require(roadmap["passed"], "independent point-orbit audit absent")
    expected = {
        f"single19-shape{entry['shape']}-high21-{orbit[0]}"
        for entry in roadmap["classes"]
        for orbit in entry["point_orbits"]
    }
    require(
        len(results) == len({row["id"] for row in results}) == 38
        and {row["id"] for row in results} == expected == set(model_audits),
        "missing, extra, or duplicated sole-degree19 cases",
    )
    reports = []
    first_control_inputs = None
    for record in results:
        name = record["id"]
        require(read(RAW / name / "result.json") == record, "per-case result mismatch")
        model_path, row_path = (
            RAW / "input" / f"{name}.pbtxt",
            RAW / "input" / f"{name}-rows.json.gz",
        )
        prior = model_audits[name]
        require(
            prior["passed"]
            and sha(model_path) == record["model_sha256"] == prior["model_sha256"]
            and sha(row_path) == record["rows_sha256"] == prior["rows_sha256"],
            "model hash mismatch",
        )
        proto = text_format.Parse(model_path.read_text(), cp_model_pb2.CpModelProto())
        require(
            len(proto.variables) == 4368
            and all(
                v.name == f"block_{i}" and list(v.domain) == [0, 1]
                for i, v in enumerate(proto.variables)
            ),
            "wrong block variable ordering or domains",
        )
        rows = []
        for constraint in proto.constraints:
            require(
                constraint.WhichOneof("constraint") == "linear"
                and not constraint.enforcement_literal
                and len(constraint.linear.domain) == 2,
                "conditional or nonlinear raw row",
            )
            row = constraint.linear
            lower, upper = row.domain
            rows.append(
                [
                    list(row.vars),
                    list(row.coeffs),
                    None if lower == -(1 << 63) else lower,
                    None if upper == (1 << 63) - 1 else upper,
                ]
            )
        require(read(row_path) == {"width": 4368, "rows": rows}, "LP rows differ from raw proto")
        primal_path = RAW / name / "primal.json.gz"
        require(sha(primal_path) == record["primal_sha256"], "primal hash mismatch")
        primal = read(primal_path)
        checked = check_vector(primal, record, rows)
        reports.append(
            {
                "id": name,
                "passed": True,
                "rows_checked": len(rows),
                "model_sha256": sha(model_path),
                "primal_sha256": sha(primal_path),
                **checked,
            }
        )
        if first_control_inputs is None:
            first_control_inputs = primal, record, rows
    rejected = []
    primal, record, rows = first_control_inputs
    for control in (
        "truncated",
        "nan",
        "boolean",
        "domain",
        "wrong_id",
        "changed_fixed_value",
        "fractionality",
        "false_cover",
        "duplicate_column",
    ):
        p, r, rs = copy.deepcopy((primal, record, rows))
        if control == "truncated":
            p["values"].pop()
        elif control == "nan":
            p["values"][0] = float("nan")
        elif control == "boolean":
            p["values"][0] = True
        elif control == "domain":
            p["values"][0] = 2.0
        elif control == "wrong_id":
            p["id"] = "wrong"
        elif control == "changed_fixed_value":
            p["values"][0] = 0.0
        elif control == "fractionality":
            r["primal_metrics"]["fractional_variables"] += 1
        elif control == "false_cover":
            r["cover_found"] = True
        else:
            rs[0][0].append(rs[0][0][0])
            rs[0][1].append(rs[0][1][0])
        try:
            check_vector(p, r, rs)
        except ValueError:
            rejected.append(control)
        else:
            raise ValueError(f"damaged primal accepted: {control}")
    maximum = max(Fraction(*r["exact_row_residual"]) for r in reports)
    result = {
        "passed": True,
        "cases": reports,
        "complete_case_count": 38,
        "maximum_exact_row_residual": [maximum.numerator, maximum.denominator],
        "maximum_row_residual_float": float(maximum),
        "exactly_rational_feasible": sum(r["exactly_rational_feasible"] for r in reports),
        "damaged_controls_rejected": rejected,
        "checker_sha256": sha(Path(__file__)),
        "metadata_sha256": sha(RAW / "metadata.json"),
        "results_sha256": sha(RAW / "results.json.gz"),
        "model_audit_sha256": sha(audit_path),
        "scope": "Exact residuals of saved binary floats in all38 audited conditional models. "
        "All vectors are fractional and only numerically feasible; no cover or exclusion.",
    }
    (HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: value for k, value in result.items() if k != "cases"}))


if __name__ == "__main__":
    main()
