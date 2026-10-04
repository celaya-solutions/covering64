# Document:    Independent Primal Fractionality and Rounding Spot Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      f1d926b9c5770264fae2105d84beacc2df7ce1536d2f89775eb91d35d213b67c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import gzip
import hashlib
import itertools
import json
import math
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PRIMALS = REPO / "experiments/scratch/four-seven-lp-primal-inspection-20261003"
SCREEN = REPO / "experiments/scratch/four-seven-link-lp-full"
SELECTED = ("cycle-069", "cycle-111", "matching-029", "matching-030", "matching-097")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    metadata = json.loads((PRIMALS / "metadata.json").read_text())
    for name, expected in metadata["inputs"].items():
        require(digest(SCREEN / name) == expected, "frozen input hash mismatch")
    records = json.loads(gzip.decompress((PRIMALS / "results.json.gz").read_bytes()))
    summaries = {r["id"]: r for r in records}
    blocks = list(itertools.combinations(range(1, 17), 5))
    triples = set(itertools.combinations(range(1, 17), 3))
    epsilon = Fraction(1, 10_000_000)
    output = []
    for identifier in SELECTED:
        saved = summaries[identifier]
        path = PRIMALS / identifier
        primal = json.loads(gzip.decompress((path / "primal.json.gz").read_bytes()))
        raw = primal["values"]
        require(len(raw) == 4768 and all(math.isfinite(v) for v in raw), "primal shape")
        values = [Fraction.from_float(v) for v in raw]
        box_residual = max(max(-v, v - 1, 0) for v in values)
        rows_payload = json.loads(
            gzip.decompress((SCREEN / f"{saved['case']}-rows.json.gz").read_bytes())
        )
        rows = rows_payload["rows"] + [[[i], [1], 1, 1] for i in primal["fixed_ids"]]
        require(len(rows) == primal["rows"] == 4277 and primal["width"] == 4768, "row dimensions")
        residual = Fraction(0)
        for indices, coefficients, lower, upper in rows:
            total = sum(values[i] * c for i, c in zip(indices, coefficients, strict=True))
            if lower is not None:
                residual = max(residual, lower - total)
            if upper is not None:
                residual = max(residual, total - upper)
        require(box_residual <= epsilon and residual <= epsilon, "numerical feasibility")
        require(
            abs(float(residual) - saved["lp"]["max_row_violation"]) < 1e-12,
            "saved floating residual mismatch",
        )
        clipped = [max(Fraction(0), min(Fraction(1), v)) for v in values[:4368]]
        metric = dict(
            fractional_block_mass=float(sum(min(v, 1 - v) for v in clipped)),
            fractional_block_count=sum(epsilon < v < 1 - epsilon for v in clipped),
            near_one_blocks=sum(v >= 1 - epsilon for v in clipped),
            near_zero_blocks=sum(v <= epsilon for v in clipped),
            threshold_half_count=sum(v >= Fraction(1, 2) for v in clipped),
            fractional_double_count=sum(epsilon < v < 1 - epsilon for v in values[4368:]),
        )
        for key, value in metric.items():
            require(abs(value - saved["lp"][key]) < 1e-12, "metric mismatch: " + key)
        chosen = sorted(sorted(range(4368), key=lambda i: (-values[i], i))[:64])
        require(chosen == saved["rounding"]["ids"], "rounding indices")
        canonical = "".join(" ".join(map(str, blocks[i])) + "\n" for i in chosen)
        require((path / "rounded-top64.txt").read_text() == canonical, "rounding file")
        covered = {t for i in chosen for t in itertools.combinations(blocks[i], 3)}
        missing = sorted(triples - covered)
        reports = json.loads((path / "rounded-checks.json").read_text())
        require(
            [list(t) for t in missing]
            == reports["package"]["uncovered"]
            == reports["standalone"]["uncovered"],
            "rounded deficit reports",
        )
        require(len(missing) == saved["rounding"]["uncovered_count"] > 0, "rounded deficit")
        require(
            reports["package"]["valid"] is False and reports["standalone"]["valid"] is False,
            "partial candidate status",
        )
        require(
            digest(path / "rounded-top64.txt") == saved["rounding"]["canonical_sha256"],
            "candidate hash",
        )
        output.append(
            dict(
                id=identifier,
                valid_audit=True,
                metrics=metric,
                exact_binary_float_row_residual=[residual.numerator, residual.denominator],
                numerical_row_residual=float(residual),
                domain_residual=float(box_residual),
                uncovered=len(missing),
                primal_sha256=digest(path / "primal.json.gz"),
                rounded_sha256=digest(path / "rounded-top64.txt"),
            )
        )
    result = dict(
        valid=True,
        selected=list(SELECTED),
        results=output,
        source_sha256=digest(Path(__file__)),
        metadata_sha256=digest(PRIMALS / "metadata.json"),
        summaries_sha256=digest(PRIMALS / "results.json.gz"),
        method="Exact rational arithmetic on the stored binary floats, independent "
        "lexicographic rounding and triple recount; no optimizer called.",
        scope="Five numerical primal spot checks. Small nonzero row residuals are not "
        "exact primal witnesses. Every rounded candidate is incomplete.",
    )
    (HERE / "independent-spot-check.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
