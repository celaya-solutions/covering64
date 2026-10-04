# Document:    Independent Stored Primal Audit for the Surviving Link Hull
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      ddd4c1bdaf2ad77fde5e250388441bdffd04da45c2f48cf49cbad6acdff0e5d6
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import gzip
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MODELS = REPO / "experiments/scratch/four-seven-template-hull-20261003"
RUN = REPO / "experiments/scratch/four-seven-template-hull-lp-20261003"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compressed(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def main():
    manifest = json.loads((MODELS / "manifest.json").read_text())
    summary = json.loads((RUN / "results.json").read_text())
    require([r["case"] for r in summary] == ["cycle", "matching"], "run completeness")
    records = []
    for saved in summary:
        case = saved["case"]
        expected = next(r for r in manifest["cases"] if r["case"] == case)
        matrix_path = MODELS / case / "extended-rows.json.gz"
        primal_path = RUN / case / "primal.json.gz"
        require(digest(matrix_path) == expected["extended_rows_sha256"], "matrix hash")
        require(digest(primal_path) == saved["primal_sha256"], "primal hash")
        model, primal = compressed(matrix_path), compressed(primal_path)
        require(primal["matrix_sha256"] == digest(matrix_path), "primal matrix linkage")
        require(primal["width"] == model["width"] == len(primal["values"]), "primal width")
        raw = primal["values"]
        require(all(type(v) in (float, int) and math.isfinite(v) for v in raw), "primal values")
        active = {i: Fraction(value) for i, value in enumerate(raw) if value != 0}
        domain = max(
            [Fraction(0), *(-v for v in active.values()), *(v - 1 for v in active.values())]
        )
        row_residual = Fraction(0)
        for indices, coefficients, lower, upper in model["rows"]:
            total = sum(
                active[i] * coefficient
                for i, coefficient in zip(indices, coefficients, strict=True)
                if i in active
            )
            if lower is not None:
                row_residual = max(row_residual, lower - total)
            if upper is not None:
                row_residual = max(row_residual, total - upper)
        epsilon = Fraction(1, 10_000_000)
        require(domain <= epsilon and row_residual <= epsilon, "numerical primal feasibility")
        require(
            abs(float(row_residual) - saved["primal_metrics"]["max_row_violation"]) < 1e-12,
            "floating residual report",
        )
        blocks = [active.get(i, Fraction(0)) for i in range(4368)]
        fractional = sum(epsilon < v < 1 - epsilon for v in blocks)
        mass = sum(min(v, 1 - v) for v in blocks)
        require(domain == 0, "nonzero domain residual requires clipping before mass comparison")
        require(
            fractional == saved["primal_metrics"]["fractional_block_count"], "fractionality count"
        )
        require(
            abs(float(mass) - saved["primal_metrics"]["fractional_block_mass"]) < 1e-12,
            "fractionality mass",
        )
        integrality = max(min(abs(v), abs(1 - v)) for v in blocks)
        selected = sum(v >= Fraction(1, 2) for v in blocks)
        require(
            integrality > epsilon and saved["integral_blocks"]["near_integral"] is False,
            "unexpected integral candidate",
        )
        require(selected == saved["integral_blocks"]["selected_block_count"], "threshold count")
        positive_templates = sum(v > epsilon for i, v in active.items() if i >= 4768)
        require(
            positive_templates == saved["primal_metrics"]["positive_template_weights"],
            "template count",
        )
        records.append(
            dict(
                case=case,
                valid_numerical_primal=True,
                checked_columns=model["width"],
                checked_rows=len(model["rows"]),
                domain_residual=[domain.numerator, domain.denominator],
                exact_binary_row_residual=[row_residual.numerator, row_residual.denominator],
                numerical_row_residual=float(row_residual),
                fractional_blocks=fractional,
                fractional_mass=float(mass),
                positive_templates=positive_templates,
                near_integral=False,
                selected_at_half=selected,
                primal_sha256=digest(primal_path),
                matrix_sha256=digest(matrix_path),
            )
        )
    result = dict(
        valid=True,
        source_sha256=digest(Path(__file__)),
        result_sha256=digest(RUN / "results.json"),
        manifest_sha256=digest(MODELS / "manifest.json"),
        cases=records,
        scope="Exact rational recount of stored binary floats confirms numerical residuals. "
        "Neither vector is an exact rational feasible witness or an integer cover.",
    )
    (HERE / "lp-primal-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    (HERE / "lp-result-summary.json").write_bytes((RUN / "results.json").read_bytes())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
