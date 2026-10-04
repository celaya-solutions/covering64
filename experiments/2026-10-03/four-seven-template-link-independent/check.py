# Document:    Independent Template Link Certificate Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check exact sparse certificates against a frozen matrix and seven raw fixed rows."""

import argparse
import copy
import gzip
import importlib.util
import json
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW_PATH = HERE.parent / "four-seven-link-lp-independent/check.py"
SPEC = importlib.util.spec_from_file_location("independent_raw_checker", RAW_PATH)
RAW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RAW)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_directory", type=Path)
    parser.add_argument("representative")
    parser.add_argument("certificate_name")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    RAW.require(not args.output.exists(), "refusing to overwrite completed replay")
    folder = args.case_directory
    matrix_path = folder / "extended-rows.json.gz"
    fixed_path = folder / args.representative / "fixed-rows.json"
    certificate_path = folder / args.representative / args.certificate_name
    matrix = json.loads(gzip.decompress(matrix_path.read_bytes()))
    fixed = json.loads(fixed_path.read_text())
    certificate = json.loads(certificate_path.read_text())
    RAW.require(fixed["id"] == args.representative and fixed["case"] == folder.name,
                "wrong fixed-row scope")
    RAW.require(fixed["base_matrix_sha256"] == RAW.sha(matrix_path), "matrix hash mismatch")
    RAW.require(fixed["width"] == matrix["width"] == certificate["checked_columns"],
                "wrong model width")
    RAW.require(matrix["variable_bounds"] ==
                "Every variable has bounds [0,1]; all are continuous in this LP."
                and certificate["box_bounds"] == [0, 1], "unsupported variable bounds")
    catalog = json.loads((HERE.parent / "four-seven-link-orbits/result.json").read_text())
    rep = next(r for group in catalog["cases"] if group["case"] == folder.name
               for r in group["representatives"] if r["id"] == args.representative)
    block_ids = {block: i for i, block in enumerate(combinations(range(1, 17), 5))}
    ids = [block_ids[(1, 2, 3, *edge)] for edge in rep["edges"]]
    RAW.require(fixed["rows"] == [[[i], [1], 1, 1] for i in ids], "wrong seven fixed rows")
    rows = matrix["rows"] + fixed["rows"]
    RAW.require(certificate["checked_rows"] == len(rows), "wrong model row count")
    checked = RAW.check_certificate(rows, matrix["width"], certificate)
    controls = []
    for control in ("rhs", "box", "gap", "width", "duplicate_weight", "zero_denominator",
                    "out_of_range_row", "nonboolean_claim"):
        damaged = copy.deepcopy(certificate)
        if control == "rhs":
            damaged["rhs_numerator"] += 1
        elif control == "box":
            damaged["box_max_numerator"] += 1
        elif control == "gap":
            damaged["gap"][0] += 1
        elif control == "width":
            damaged["checked_columns"] += 1
        elif control == "duplicate_weight":
            damaged["weights"].append(damaged["weights"][0])
        elif control == "zero_denominator":
            damaged["denominator"] = 0
        elif control == "out_of_range_row":
            damaged["weights"][0][0] = len(rows)
        else:
            damaged["proves_infeasible"] = 1
        try:
            RAW.check_certificate(rows, matrix["width"], damaged)
        except ValueError:
            controls.append(control)
        else:
            raise ValueError(f"damaged certificate accepted: {control}")
    result = {"passed": True, "representative": args.representative, "case": folder.name,
              **checked, "fixed_ids": ids, "matrix_sha256": RAW.sha(matrix_path),
              "fixed_rows_sha256": RAW.sha(fixed_path),
              "certificate_sha256": RAW.sha(certificate_path),
              "checker_sha256": RAW.sha(Path(__file__)), "raw_checker_sha256": RAW.sha(RAW_PATH),
              "damaged_controls_rejected": controls,
              "scope": "Exact certificate and fixed-row replay only. Applicability to integer "
                       "regular four-sevenfold covers also requires the separate full-template "
                       "encoding audit for this exact base matrix. No unrestricted bound."}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
