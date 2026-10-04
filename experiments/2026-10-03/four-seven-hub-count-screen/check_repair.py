# Document:    Independent Replay of Hub Numerical Repairs
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      f0cb90bdba8322045ee22be534dd77d4e1012c322d017a01b74fbe919265dbca
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check new duals against the original independently audited campaign models."""

import copy
import gzip
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW_PATH = HERE.parent / "four-seven-link-lp-independent/check.py"
SPEC = importlib.util.spec_from_file_location("independent_raw_replay", RAW_PATH)
RAW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RAW)
require, sha = RAW.require, RAW.sha
ARCHIVE = ROOT / "experiments/scratch/four-seven-hub-numerical-repair-v1.0.0"
CAMPAIGN = ROOT / "experiments/scratch/four-seven-hub-campaign-v1.0.0"


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def replay(item, expected):
    key = (tuple(item["hub_case"]), item["id"])
    require(key in expected, "unexpected repaired subcase")
    m4, z = key[0]
    folder = CAMPAIGN / f"m4-{m4}-z-{z}"
    audit = read(HERE / f"m4-{m4}-z-{z}-audit.json")
    require(sha(HERE / f"m4-{m4}-z-{z}-audit.json") ==
            (HERE / f"m4-{m4}-z-{z}-audit.sha256").read_text().strip(), "damaged audit")
    require(audit["passed"] and audit["complete_selected_coverage"], "unaudited child")
    require(audit["checker_sha256"] == sha(RAW_PATH), "raw checker changed")
    metadata = read(folder / "metadata.json")
    require(audit["metadata_sha256"] == sha(folder / "metadata.json"), "metadata changed")
    require(audit["results_sha256"] == sha(folder / "results.json.gz"), "results changed")
    old = next(row for row in read(folder / "results.json.gz") if row["id"] == item["id"])
    require(not old["proves_infeasible"], "repair was already excluded")
    require(item["fixed_ids"] == old["fixed_ids"] and item["case"] == old["case"],
            "repair changed fixed link")
    model = folder / f"{item['case']}-base.pbtxt"
    rows_path = folder / f"{item['case']}-rows.json.gz"
    hashes = metadata["models"][item["case"]]
    require(sha(model) == hashes["model_sha256"], "model changed")
    require(sha(rows_path) == hashes["rows_sha256"] == item["row_archive_sha256"],
            "row archive changed")
    require(item["row_archive"] == str(rows_path.relative_to(ROOT)), "wrong archive path")
    model_report = next(row for row in audit["models"] if row["case"] == item["case"])
    require(model_report["identical_proto"] and model_report["model_sha256"] == sha(model),
            "model disconnected from encoding audit")
    proto, base = RAW.proto_rows(model)
    require(read(rows_path) == {"width": len(proto.variables), "rows": base},
            "matrix differs from audited protobuf")
    rows = base + [[[index], [1], 1, 1] for index in item["fixed_ids"]]
    require(item["checked_rows"] == len(rows) and
            item["checked_columns"] == len(proto.variables), "wrong dimensions")
    require(item["proves_infeasible"] is True and item["certificates"], "missing claim")
    checked = [RAW.check_certificate(rows, len(proto.variables), certificate)
               for certificate in item["certificates"]]
    require(any(result["proves_infeasible"] for result in checked), "no positive exact gap")
    return {"id": item["id"], "hub_case": item["hub_case"], "case": item["case"],
            "model_sha256": sha(model), "matrix_sha256": sha(rows_path),
            "original_audit_sha256": sha(HERE / f"m4-{m4}-z-{z}-audit.json"),
            "certificates": checked, "proves_infeasible": True}


def main():
    summary = read(HERE / "campaign-summary.json")
    expected = {(tuple(row["hub_case"]), row["id"]) for row in summary["inconclusive"]}
    require(len(expected) == 7, "unexpected repair inventory")
    metadata = read(ARCHIVE / "metadata.json")
    require(metadata["summary_sha256"] == sha(HERE / "campaign-summary.json"),
            "repair used a different inventory")
    require(metadata["source_sha256"] == sha(ARCHIVE / "repair_numerics.py") ==
            sha(HERE / "repair_numerics.py"), "repair source mismatch")
    require(metadata["solver_helper_sha256"] == sha(ARCHIVE / "four_seven_link_lp.py"),
            "solver source mismatch")
    results = read(ARCHIVE / "results.json.gz")
    require(len(results) == 7 and
            {(tuple(row["hub_case"]), row["id"]) for row in results} == expected,
            "incomplete or duplicate repair inventory")
    checks = [replay(item, expected) for item in results]
    damaged = []
    for field, value in (("denominator", 0), ("gap", [1, 0]),
                         ("checked_columns", 1), ("rhs_numerator", 0),
                         ("box_max_numerator", -1), ("proves_infeasible", False)):
        item = copy.deepcopy(results[0])
        item["certificates"][0][field] = value
        damaged.append((field, item))
    for field, value in (("fixed_ids", []), ("row_archive_sha256", "0" * 64),
                         ("checked_rows", 1), ("hub_case", [9, 9])):
        item = copy.deepcopy(results[0])
        item[field] = value
        damaged.append((field, item))
    controls = []
    for name, item in damaged:
        try:
            replay(item, expected)
        except (ValueError, AssertionError):
            controls.append({"mutation": name, "rejected": True})
        else:
            raise AssertionError(f"damaged control accepted: {name}")
    previous = read(HERE / "combined-audit.json")
    require(previous["passed"], "prior combination failed")
    exclusions = copy.deepcopy(previous["case_exclusions_by_id"])
    for result in checks:
        require(result["hub_case"] not in exclusions[result["id"]], "double-counted case")
        exclusions[result["id"]].append(result["hub_case"])
    fully = sorted(rid for rid, cases in exclusions.items() if len(cases) == 6)
    report = {"passed": True, "checker_sha256": sha(Path(__file__)),
              "raw_checker_sha256": sha(RAW_PATH),
              "results_sha256": sha(ARCHIVE / "results.json.gz"),
              "original_combined_audit_sha256": sha(HERE / "combined-audit.json"),
              "checks": checks, "damaged_controls": controls,
              "conditional_exclusions": sum(map(len, exclusions.values())),
              "unresolved_numerical_cases": 0, "fully_excluded_ids": fully,
              "case_exclusions_by_id": exclusions,
              "scope": "Only seven fixed-link/hub-count subcases in the regular "
                       "four-sevenfold branch."}
    (HERE / "numerical-repair-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    certificates = [{key: value for key, value in result.items() if key != "phase"}
                    for result in results]
    (HERE / "numerical-repair-certificates.json.gz").write_bytes(gzip.compress(
        (json.dumps(certificates, indent=2) + "\n").encode(), mtime=0))
    print(json.dumps({key: report[key] for key in
                      ("passed", "conditional_exclusions", "fully_excluded_ids",
                       "unresolved_numerical_cases")}))


if __name__ == "__main__":
    main()
