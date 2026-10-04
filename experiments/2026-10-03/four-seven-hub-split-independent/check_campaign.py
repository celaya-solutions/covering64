# Document:    Independent Six Case Hub Campaign Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Replay completed children and count only intersections of all six exclusions."""

import argparse
import importlib.util
import json
from itertools import product
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW_PATH = HERE.parent / "four-seven-link-lp-independent/check.py"
SPEC = importlib.util.spec_from_file_location("raw_first_link_checker", RAW_PATH)
RAW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RAW)
CASES = tuple(product((0, 1), range(3)))
NAMES = {f"m4-{m4}-z-{z}": (m4, z) for m4, z in CASES}
require, sha = RAW.require, RAW.sha


def read(path):
    return json.loads(path.read_text())


def read_proto(path):
    return text_format.Parse(path.read_text(), cp_model_pb2.CpModelProto())


def expected_representatives():
    catalog = read(HERE.parent / "four-seven-link-orbits/result.json")
    original = {r["id"]: (group["case"], r) for group in catalog["cases"]
                for r in group["representatives"]}
    require(len(original) == 258, "wrong original orbit count")
    excluded = set()
    for path, count in (
        (HERE.parent / "four-seven-link-lp-independent/full-v1.1.0-final-audit.json", 100),
        (HERE.parent / "four-seven-blossom-independent/blossom-screen-audit.json", 2),
    ):
        audit = read(path)
        require(audit["complete_selected_coverage"] and audit["excluded"] == count,
                "prior checked exclusions absent")
        ids = {r["id"] for r in audit["checks"] if r["proves_infeasible"]}
        require(len(ids) == count and not excluded.intersection(ids), "bad prior exclusion IDs")
        excluded.update(ids)
    result = {rid: entry for rid, entry in original.items() if rid not in excluded}
    require(len(result) == 156, "wrong remaining catalog size")
    return result


def check_campaign_header(folder):
    metadata = read(folder / "metadata.json")
    require(metadata["cases"] == [list(case) for case in CASES], "incomplete hub partition")
    require(metadata["maximum_parallel_processes"] == 2
            and metadata["seconds_per_stage"] == 10, "changed campaign budget")
    require(sha(folder / "representatives.json") == metadata["representatives_sha256"],
            "campaign representative hash")
    require(sha(folder / "independent-hub-audit.json") == metadata["audit_sha256"],
            "campaign split audit hash")
    split = read(folder / "independent-hub-audit.json")
    require(split["passed"] and split["helper_sha256"] ==
            metadata["sources"]["scripts/four_seven_hub_split.py"], "unaudited split helper")
    require(sha(folder / "four_seven_hub_campaign.py") ==
            metadata["sources"]["scripts/four_seven_hub_campaign.py"], "launcher hash")
    expected = expected_representatives()
    selected = read(folder / "representatives.json")
    actual = {rep["id"]: (group["case"], rep) for group in selected["cases"]
              for rep in group["representatives"]}
    require(sum(len(group["representatives"]) for group in selected["cases"]) == len(actual),
            "duplicate selected representative")
    require(actual == expected, "selected catalog differs from 156 checked survivors")
    return metadata, split, expected


def check_child(folder, name, metadata, split, expected):
    m4, z = NAMES[name]
    process = read(folder / f"{name}-process.json")
    require(process["case"] == [m4, z] and process["returncode"] == 0, "unfinished child")
    child = folder / name
    child_metadata = read(child / "metadata.json")
    require(child_metadata["hub_count_split"] == [m4, z], "wrong child hub case")
    require(child_metadata["case"] == "both" and child_metadata["limit"] is None,
            "restricted representative selection")
    require(sha(child / "representatives.json") == metadata["representatives_sha256"],
            "child selected different representatives")
    require(set(child_metadata["models"]) == {"cycle", "matching"}, "missing child base")
    for source, digest in metadata["sources"].items():
        filename = Path(source).name
        if filename != "four_seven_hub_campaign.py":
            require(sha(child / filename) == digest, "child source differs from campaign")
    model_reports = []
    for case in ("cycle", "matching"):
        prior = next(r for r in split["models"]
                     if (r["case"], r["m4"], r["z"]) == (case, m4, z))
        audited = ROOT / "experiments/scratch/four-seven-hub-split-independent" / (
            f"{case}-m4-{m4}-z-{z}.pbtxt")
        require(sha(audited) == prior["model_sha256"], "audited split model changed")
        actual = child / f"{case}-base.pbtxt"
        require(read_proto(actual) == read_proto(audited), "child differs from audited model")
        model_reports.append({"case": case, "model_sha256": sha(actual),
                              "audited_model_sha256": sha(audited), "identical_proto": True})
    result = RAW.audit_run(child)
    require(result["records"] == 156 and {r["id"] for r in result["checks"]} == set(expected),
            "child lacks complete checked representative coverage")
    return {"passed": True, "hub_case": [m4, z], "models": model_reports,
            "campaign_metadata_sha256": sha(folder / "metadata.json"),
            "campaign_checker_sha256": sha(Path(__file__)), **result}


def combine(reports, expected):
    require(len(reports) == 6 and {tuple(r["hub_case"]) for r in reports} == set(CASES),
            "all six distinct case audits required")
    exclusions = {rid: [] for rid in expected}
    for report in reports:
        checks = report["checks"]
        require(len(checks) == len(expected) and {r["id"] for r in checks} == set(expected),
                "incomplete per-case coverage")
        for row in checks:
            require(type(row["proves_infeasible"]) is bool, "nonboolean exclusion flag")
            if row["proves_infeasible"]:
                exclusions[row["id"]].append(report["hub_case"])
    complete = sorted(rid for rid, cases in exclusions.items() if len(cases) == 6)
    return {"fully_excluded_ids": complete, "remaining_ids": sorted(set(expected) - set(complete)),
            "case_exclusions_by_id": exclusions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--child", choices=tuple(NAMES))
    args = parser.parse_args()
    metadata, split, expected = check_campaign_header(args.campaign)
    args.output.mkdir(parents=True, exist_ok=True)
    reports = []
    for name in ([args.child] if args.child else NAMES):
        path = args.output / f"{name}-audit.json"
        digest_path = args.output / f"{name}-audit.sha256"
        if path.exists():
            require(sha(path) == digest_path.read_text().strip(), "stored child audit damaged")
            report = read(path)
            child = args.campaign / name
            require(report["passed"] and report["campaign_checker_sha256"] == sha(Path(__file__))
                    and report["checker_sha256"] == sha(RAW_PATH)
                    and report["metadata_sha256"] == sha(child / "metadata.json")
                    and report["results_sha256"] == sha(child / "results.json.gz")
                    and report["campaign_metadata_sha256"] == sha(args.campaign / "metadata.json"),
                    "stored child audit no longer matches frozen inputs")
        else:
            report = check_child(args.campaign, name, metadata, split, expected)
            path.write_text(json.dumps(report, indent=2) + "\n")
            digest_path.write_text(sha(path) + "\n")
        reports.append(report)
        print(json.dumps({"child": name, "passed": True,
                          "excluded": report["excluded"]}), flush=True)
    if args.child:
        return
    process_results = read(args.campaign / "process-results.json")
    require(len(process_results) == 6 and {tuple(p["case"]) for p in process_results} == set(CASES)
            and all(p["returncode"] == 0 for p in process_results), "campaign incomplete")
    path = args.output / "combined-audit.json"
    require(not path.exists(), "refusing to overwrite combined audit")
    result = {"passed": True, "records": sum(r["records"] for r in reports),
              "checked_hub_cases": [list(case) for case in CASES],
              "child_audit_sha256": {name: sha(args.output / f"{name}-audit.json")
                                     for name in NAMES},
              "checker_sha256": sha(Path(__file__)), **combine(reports, expected),
              "scope": "Only fixed-first-link integer regular four-sevenfold models; "
                       "an ID is excluded only by checked certificates in all six hub cases."}
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": True, "fully_excluded": len(result["fully_excluded_ids"])}))


if __name__ == "__main__":
    main()
