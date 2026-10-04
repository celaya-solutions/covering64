# Document:    Targeted 108 Hull LP Readback Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      38c44612b1d5d3af73372b998b0c525abcdc540f39f5ac14c1c7a350a29a77c2
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read saved numerical primals without invoking the builder or any solver."""

import gzip
import hashlib
import json
from fractions import Fraction
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/four-seven-template-hub-refresh-108-20261003"


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def primal_check(values, width, rows):
    require(width == 52936, "width")
    require(len({i for i, _ in values}) == len(values), "duplicate sparse column")
    require(all(type(i) is int and 0 <= i < width and 0 <= x <= 1 for i, x in values),
            "sparse domain")
    vector = {i: Fraction(x) for i, x in values}
    worst = Fraction(0)
    for ids, coeff, lower, upper in rows:
        activity = sum(c * vector.get(i, 0) for i, c in zip(ids, coeff, strict=True))
        if lower is not None:
            worst = max(worst, Fraction(lower) - activity)
        if upper is not None:
            worst = max(worst, activity - Fraction(upper))
    require(worst < Fraction(1, 100_000_000), "numerical row residual")
    return worst


def main():
    matrix = ROOT / ("experiments/scratch/four-seven-template-hull-refresh-108-20261003/"
                     "matching/extended-rows.json.gz")
    require(sha(matrix) == "e9b2289291479c5f1119f432f0131d8fda8130ace2e64c773cf93dd8928ceade",
            "frozen matrix")
    payload = load(matrix)
    cp_dir = HERE.parent / "four-seven-template-cp-restricted"
    manifest = load(cp_dir / "manifest.json")
    eligibility = load(cp_dir / "independent-audit.json")
    require(eligibility["passed"] and eligibility["manifest_sha256"] ==
            sha(cp_dir / "manifest.json"), "case eligibility")
    selected = {r["case"]: r for r in manifest["cases"]}
    results = load(RAW / "results.json")
    require({r["id"] for r in results} == set(selected) and len(results) == 2, "case count")
    metadata = load(RAW / "metadata.json")
    for path, digest in metadata["input_hashes"].items():
        require(sha(ROOT / path) == digest, "source or input changed")
    blocks = list(combinations(range(1, 17), 5))
    counts = [len(set(b) & {4, 8, 12, 16}) for b in blocks]
    four = [i for i, n in enumerate(counts) if n == 4]
    many = [i for i, n in enumerate(counts) if n >= 3]
    reports, controls = [], []
    for result in results:
        target = RAW / result["id"]
        source = selected[result["id"]]
        m4, z = source["hub_case"]
        fixed = source["fixed_ids"]
        require(result["hub_case"] == [m4, z] and result["fixed_ids"] == fixed, "scope")
        rows = [*payload["rows"], [four, [1] * len(four), m4, m4],
                [many, [1 if counts[i] == 3 else 4 for i in many], 4 + z, 4 + z],
                *[[[i], [1], 1, 1] for i in fixed]]
        saved = load(target / "full-rows.json.gz")
        require(saved == dict(width=52936, rows=rows) and len(rows) == 4559, "all rows")
        require(sha(target / "full-rows.json.gz") == result["full_rows_sha256"], "matrix link")
        require(load(target / "result.json") == result, "saved result")
        require(result["feasibility_lp"]["status_name"] == "OPTIMAL" and
                not result["certificate_pending_replay"] and
                not result["independently_excluded"], "classification")
        require(sha(target / "feasibility-solver.log") ==
                result["feasibility_lp"]["log_sha256"], "solver log")
        sparse = load(target / "sparse-primal.json.gz")
        worst = primal_check(sparse["values"], sparse["width"], rows)
        for label, values, width in (
            ("wrong width", sparse["values"], 52935),
            ("duplicate column", sparse["values"] + [sparse["values"][0]], 52936),
            ("negative value", [[0, -1]], 52936),
            ("zero vector", [], 52936),
        ):
            try:
                primal_check(values, width, rows)
            except ValueError:
                controls.append(dict(case=result["id"], mutation=label, rejected=True))
            else:
                raise ValueError("damaged primal accepted")
        reports.append(dict(id=result["id"], passed=True, rows=4559, columns=52936,
                            exact_binary_max_numerical_residual=str(worst),
                            numerical_residual=float(worst),
                            sparse_primal_sha256=sha(target / "sparse-primal.json.gz")))
    audit = dict(passed=True, checker_sha256=sha(Path(__file__)),
                 results_sha256=sha(RAW / "results.json"), cases=reports,
                 damaged_controls=controls, solver_calls=0,
                 scope="Numerical readback only; no exact feasibility or exclusion theorem.")
    (HERE / "readback-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit))


if __name__ == "__main__":
    main()
