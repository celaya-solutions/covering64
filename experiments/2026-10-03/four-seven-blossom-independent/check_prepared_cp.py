# Document:    Independent Full Cut CP Pilot Composition Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Concatenate independently audited suffixes and verify only seven new fixed-link rows."""

import hashlib
import json
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREPARED = ROOT / "experiments/scratch/four-seven-blossom-cp-v1.1.0"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_proto(path):
    return text_format.Parse(path.read_text(), cp_model_pb2.CpModelProto())


def main():
    metadata = json.loads((PREPARED / "prepared.json").read_text())
    require(metadata["seconds_per_case"] == 300 and metadata["workers_per_case"] == 2
            and metadata["maximum_simultaneous_cases"] == 2, "changed pilot budget")
    for name, digest in metadata["sources"].items():
        require(sha(PREPARED / name) == digest, "frozen source changed")
    facet_audit = json.loads(
        (HERE.parent / "four-seven-facet-independent/model-audit.json").read_text()
    )
    blossom_audit = json.loads((HERE / "model-audit.json").read_text())
    require(facet_audit["passed"] and blossom_audit["passed"], "prerequisite audit absent")
    rows_by_case = {}
    for case in ("cycle", "matching"):
        facet_path = (ROOT / "experiments/scratch/four-seven-facet-independent-models" /
                      f"{case}-features-facets.pbtxt")
        facet_record = next(r for r in facet_audit["models"]
                            if r["case"] == case and r["first_features"])
        blossom_path = (ROOT / "experiments/scratch/four-seven-blossom-cuts-v1.0.0" /
                        f"{case}-blossoms.pbtxt")
        blossom_record = next(r for r in blossom_audit["models"] if r["case"] == case)
        require(sha(facet_path) == facet_record["model_sha256"]
                and sha(blossom_path) == blossom_record["model_sha256"], "audited input changed")
        expected = read_proto(facet_path)
        blossoms = read_proto(blossom_path)
        expected.constraints.extend(blossoms.constraints[4270:])
        actual = read_proto(PREPARED / f"{case}-base.pbtxt")
        require(actual == expected, "combined base differs from audited concatenation")
        rows_by_case[case] = actual
    representatives = json.loads((HERE.parent / "four-seven-link-orbits/result.json").read_text())
    reps = {r["id"]: r for c in representatives["cases"] for r in c["representatives"]}
    block_ids = {b: i for i, b in enumerate(combinations(range(1, 17), 5))}
    expected_ids = {"matching-029", "matching-113", "cycle-069", "cycle-046"}
    require({r["id"] for r in metadata["cases"]} == expected_ids
            and len(metadata["cases"]) == 4, "wrong selected pilots")
    reports = []
    for entry in metadata["cases"]:
        rid = entry["id"]
        case = rid.split("-")[0]
        base = rows_by_case[case]
        fixed = [block_ids[(1, 2, 3, *edge)] for edge in reps[rid]["edges"]]
        path = PREPARED / rid / "model.pbtxt"
        require(sha(path) == entry["model_sha256"], "pilot model hash changed")
        model = read_proto(path)
        offset = len(base.constraints)
        require(len(model.variables) == 4768 and len(model.constraints) == offset + 7,
                "wrong model size")
        for i, block in enumerate(fixed):
            row = model.constraints[offset + i]
            require(row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
                    and list(row.linear.vars) == [block] and list(row.linear.coeffs) == [1]
                    and list(row.linear.domain) == [1, 1], "incorrect fixed-link row")
        del model.constraints[offset:]
        require(model == base, "pilot changed a prior base field")
        reports.append({"id": rid, "passed": True, "fixed_ids": fixed,
                        "base_rows": offset, "rows": offset + 7,
                        "model_sha256": sha(path), "all_prior_proto_fields_preserved": True})
    result = {"passed": True, "models": reports, "checker_sha256": sha(Path(__file__)),
              "prepared_sha256": sha(PREPARED / "prepared.json"),
              "scope": "Encoding composition audit only; this does not run or certify a search."}
    (HERE / "prepared-cp-v1.1-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": True, "pilots": len(reports)}))


if __name__ == "__main__":
    main()
