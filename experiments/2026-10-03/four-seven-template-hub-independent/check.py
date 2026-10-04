# Document:    Independent Combined Template and Hub Certificate Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check one combined matrix, its exact certificate, and the other five hub cases."""

import copy
import gzip
import importlib.util
import json
from itertools import combinations, product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW_PATH = HERE.parent / "four-seven-link-lp-independent/check.py"
SPEC = importlib.util.spec_from_file_location("raw_certificate_replay", RAW_PATH)
RAW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RAW)


def main():
    base_folder = ROOT / "experiments/scratch/four-seven-template-hub-priority-20261003"
    folder = base_folder / "matching-m4-0-z-1"
    matrix_path = folder / "combined-base-rows.json.gz"
    fixed_path = folder / "matching-032/fixed-rows.json"
    certificate_path = folder / "matching-032/certificate-1000000.json"
    matrix = json.loads(gzip.decompress(matrix_path.read_bytes()))
    fixed = json.loads(fixed_path.read_text())
    certificate = json.loads(certificate_path.read_text())
    original_path = ROOT / "experiments/scratch/four-seven-template-hull-20261003" / (
        "matching/extended-rows.json.gz")
    original = json.loads(gzip.decompress(original_path.read_bytes()))
    audit_path = HERE.parent / "four-seven-template-hull/independent-audit.json"
    audit = json.loads(audit_path.read_text())
    matching = next(r for r in audit["cases"] if r["case"] == "matching")
    RAW.require(audit["passed"] and matching["passed"]
                and RAW.sha(original_path) == matching["matrix_sha256"],
                "unaudited original matrix")
    RAW.require(matrix["width"] == original["width"] == 61576
                and matrix["variable_bounds"] == "Every variable lies in [0,1].",
                "changed variable bounds or width")
    RAW.require(matrix["rows"][:-2] == original["rows"], "original hull rows changed")
    blocks = list(combinations(range(1, 17), 5))
    hubs = (4, 8, 12, 16)
    four_ids = [i for i, block in enumerate(blocks) if set(hubs).issubset(block)]
    triple_terms = [(i, sum(set(t).issubset(block) for t in combinations(hubs, 3)))
                    for i, block in enumerate(blocks)
                    if any(set(t).issubset(block) for t in combinations(hubs, 3))]
    expected_hub_rows = [[four_ids, [1] * len(four_ids), 0, 0],
                         [[i for i, _ in triple_terms], [c for _, c in triple_terms], 5, 5]]
    RAW.require(matrix["rows"][-2:] == expected_hub_rows, "wrong two hub rows")
    RAW.require(fixed["id"] == "matching-032" and fixed["case"] == "matching"
                and fixed["hub_case"] == [0, 1], "wrong conditional scope")
    RAW.require(fixed["combined_matrix_sha256"] == RAW.sha(matrix_path)
                and fixed["width"] == matrix["width"], "fixed-row matrix hash or width")
    catalog = json.loads((HERE.parent / "four-seven-link-orbits/result.json").read_text())
    representative = next(r for group in catalog["cases"] if group["case"] == "matching"
                          for r in group["representatives"] if r["id"] == "matching-032")
    ids = {block: i for i, block in enumerate(blocks)}
    fixed_ids = [ids[(1, 2, 3, *edge)] for edge in representative["edges"]]
    RAW.require(fixed["rows"] == [[[i], [1], 1, 1] for i in fixed_ids], "wrong fixed link")
    rows = matrix["rows"] + fixed["rows"]
    RAW.require(certificate["checked_rows"] == len(rows) == 4559
                and certificate["box_bounds"] == [0, 1], "wrong certificate dimensions")
    checked = RAW.check_certificate(rows, matrix["width"], certificate)
    RAW.require(checked["proves_infeasible"] and checked["gap"] == [7651, 1000000],
                "no expected positive exact contradiction")
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
    hub_folder = HERE.parent / "four-seven-hub-count-screen"
    combined = json.loads((hub_folder / "combined-audit.json").read_text())
    RAW.require(combined["passed"], "prior complete hub audit absent")
    cases = [{"hub_case": [0, 1], "source": "combined-template-hub", **checked}]
    for m4, z in product((0, 1), range(3)):
        if (m4, z) == (0, 1):
            continue
        name = f"m4-{m4}-z-{z}"
        path = hub_folder / f"{name}-audit.json"
        RAW.require(RAW.sha(path) == combined["child_audit_sha256"][name], "prior audit changed")
        prior = json.loads(path.read_text())
        record = next(r for r in prior["checks"] if r["id"] == "matching-032")
        RAW.require(prior["passed"] and prior["hub_case"] == [m4, z]
                    and record["proves_infeasible"], "prior hub case not excluded")
        cases.append({"hub_case": [m4, z], "source": str(path.relative_to(ROOT)),
                      "audit_sha256": RAW.sha(path), **record})
    RAW.require({tuple(row["hub_case"]) for row in cases} == set(product((0, 1), range(3))),
                "incomplete six-case exclusion")
    result = {"passed": True, "representative": "matching-032", "fully_excluded": True,
              "certificate_replay": checked, "all_six_cases": cases,
              "original_encoding_audit_sha256": RAW.sha(audit_path),
              "original_matrix_sha256": RAW.sha(original_path),
              "combined_matrix_sha256": RAW.sha(matrix_path),
              "certificate_sha256": RAW.sha(certificate_path),
              "fixed_rows_sha256": RAW.sha(fixed_path), "fixed_ids": fixed_ids,
              "original_rows_preserved": len(original["rows"]), "hub_rows_checked": 2,
              "damaged_controls_rejected": controls, "checker_sha256": RAW.sha(Path(__file__)),
              "raw_checker_sha256": RAW.sha(RAW_PATH),
              "scope": "All six exhaustive hub cases exclude this fixed-first-link integer "
                       "regular four-sevenfold representative. No full-branch or global bound."}
    (HERE / "matching-032-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    evidence = {"audit": result, "certificate": certificate, "fixed_rows": fixed,
                "added_hub_rows": expected_hub_rows}
    (HERE / "evidence.json.gz").write_bytes(gzip.compress(
        (json.dumps(evidence) + "\n").encode(), mtime=0))
    print(json.dumps({"passed": True, "fully_excluded": "matching-032",
                      "gap": checked["gap"], "six_cases_checked": len(cases)}))


if __name__ == "__main__":
    main()
