#!/usr/bin/env python3
# Document:    Independent Matching Graph Five Diagnostic Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Recount both saved primal vectors and exact shifted-row certificates."""

import json
import math
from fractions import Fraction

from check import HERE, RAW, SOURCE, expected_case, sha


def main():
    output = HERE / "postcheck.json"
    assert not output.exists()
    gate = json.loads((HERE / "audit.json").read_text())
    assert gate["passed"] and sha(SOURCE / "manifest.json") == gate["manifest_sha256"]
    assert sha(SOURCE / "diagnostic.py") == gate["runner_sha256"]
    results = []
    for checked in gate["checked"]:
        case = checked["case"]
        folder, raw = SOURCE / case, RAW / case
        manifest = json.loads((folder / "manifest.json").read_text())
        assert sha(folder / "manifest.json") == checked["manifest_sha256"]
        result = json.loads((folder / "result.json").read_text())
        launch = json.loads((folder / "launch.json").read_text())
        assert launch == {
            "case": case,
            "gate_sha256": sha(HERE / "audit.json"),
            "workers": 1,
            "seconds": 1,
            "seed": 2026104,
            "optimization_calls": 1,
        }
        assert result["manifest_sha256"] == checked["manifest_sha256"]
        assert result["case"] == case and result["graph_index"] == 5
        assert result["optimization_calls"] == 1 and result["status"] == "OPTIMAL"
        _, rows, _, _, _ = expected_case(manifest)
        assert rows == json.loads((raw / "rows.json").read_text())
        primal = json.loads((raw / "primal.json").read_text())
        numerical_dual = json.loads((raw / "dual-numerical.json").read_text())
        variables = json.loads((raw / "all-variables.json").read_text())
        assert len(primal) == 1200 and len(numerical_dual) == 697
        assert all(math.isfinite(v) and -1e-7 <= v <= 1 + 1e-7 for v in primal)
        assert all(math.isfinite(v) for v in numerical_dual)
        values = dict(variables)
        assert len(values) == len(variables) == 2590
        assert [values[f"x_{i}"] for i in range(1200)] == primal
        residual, slacks = 0.0, []
        for row_id, (indices, coefficients, lower, upper) in enumerate(rows):
            value = math.fsum(
                coefficient * primal[index]
                for index, coefficient in zip(indices, coefficients, strict=True)
            )
            residual += max(0.0, lower - value)
            low_slack = values[f"lo_{row_id}"]
            assert math.isfinite(low_slack) and low_slack >= -1e-7
            slacks.append(low_slack)
            high_slack = 0.0
            if upper != 2**63 - 1:
                residual += max(0.0, value - upper)
                high_slack = values[f"hi_{row_id}"]
                assert math.isfinite(high_slack) and high_slack >= -1e-7
                slacks.append(high_slack)
                assert value + low_slack - high_slack <= upper + 1e-7
            assert value + low_slack - high_slack >= lower - 1e-7
        assert abs(residual - result["branch_elastic_objective"]) <= 1e-6
        assert abs(math.fsum(slacks) - result["branch_elastic_objective"]) <= 1e-6
        dual = json.loads((folder / "dual.json").read_text())
        weights, seen = [0] * 697, set()
        assert dual["denominator"] == 1000000
        for row, weight in dual["weights"]:
            assert type(row) is int and 0 <= row < 697 and row not in seen
            assert type(weight) is int and weight != 0
            assert weight >= 0 or rows[row][3] != 2**63 - 1
            seen.add(row)
            weights[row] = weight
        constant = sum(
            weight * (rows[row][2] if weight > 0 else rows[row][3])
            for row, weight in enumerate(weights)
            if weight
        )
        coefficients = [
            sum(weights[row] for row, spec in enumerate(rows) if i in spec[0]) for i in range(1200)
        ]
        box = sum(max(0, coefficient) for coefficient in coefficients)
        gap = Fraction(constant - box, dual["denominator"])
        assert gap > 0 and dual["proves_infeasible"]
        assert constant == dual["rhs_numerator"] and box == dual["box_max_numerator"]
        assert dual["gap"] == result["exact_gap"] == [gap.numerator, gap.denominator]
        assert dual["model_sha256"] == manifest["model_sha256"]
        assert dual["heavy_sha256"] == manifest["heavy_sha256"]
        assert dual["manifest_sha256"] == sha(folder / "manifest.json")
        results.append(
            {
                "case": case,
                "residual_recounted": residual,
                "exact_gap": dual["gap"],
                "maximum_abs_weight": max(map(abs, weights)),
                "seconds": result["seconds"],
                "result_sha256": sha(folder / "result.json"),
                "primal_sha256": sha(raw / "primal.json"),
                "numerical_dual_sha256": sha(raw / "dual-numerical.json"),
                "all_variables_sha256": sha(raw / "all-variables.json"),
                "exact_dual_sha256": sha(folder / "dual.json"),
            }
        )
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": sha(__file__),
        "gate_sha256": sha(HERE / "audit.json"),
        "results": results,
        "scope": "Two exact positive certificates for their fixed-heavy graph-five "
        "completion models only; no all-graph or unrestricted bound.",
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
