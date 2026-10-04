# Document:    Finalize Completed Sole-Degree-Nineteen LP Evidence
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      113dbbac4f38bec4ac084dee91c6679aa200a11dab95de6e23f17f3b1f1b971e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Finalize intact38-case results after a relative-path summary formatting failure."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    directory = args.directory.resolve()
    records_path = directory / "results.json.gz"
    records = json.loads(gzip.decompress(records_path.read_bytes()))
    manifest = json.loads((directory / "input/manifest.json").read_text())
    assert len(records) == len(manifest["cases"]) == 38
    assert {row["id"] for row in records} == {row["id"] for row in manifest["cases"]}
    for row in records:
        individual = json.loads((directory / row["id"] / "result.json").read_text())
        assert individual == row
        if "primal_sha256" in row:
            assert sha(directory / row["id"] / "primal.json.gz") == row["primal_sha256"]
    summary = {
        "scope": "Completed38-case sole-degree19 LP screen; numerical feasibility is not a cover.",
        "cases": len(records), "exact_exclusions": sum(row["proves_infeasible"] for row in records),
        "covers": sum(row["cover_found"] for row in records),
        "numerically_feasible": sum(row.get("primal_metrics", {}).get("numerically_valid", False)
                                    for row in records),
        "fractional_cases": sum(row.get("primal_metrics", {}).get("fractional_variables", 0) > 0
                                for row in records),
        "maximum_row_violation": max(row.get("primal_metrics", {}).get("maximum_row_violation", 0)
                                     for row in records),
        "maximum_domain_violation": max(row.get("primal_metrics", {}).get(
            "maximum_domain_violation", 0) for row in records),
        "total_elapsed_seconds": sum(row["elapsed_seconds"] for row in records),
        "maximum_case_elapsed_seconds": max(row["elapsed_seconds"] for row in records),
        "results_sha256": sha(records_path), "raw_archive": str(directory.relative_to(ROOT)),
        "metadata_sha256": sha(directory / "metadata.json"),
        "finalizer_sha256": sha(Path(__file__)),
        "finalization_note": "All38 solves, per-case results, and primals were saved before "
                             "the original runner's final summary writer failed when applying "
                             "relative_to(absolute ROOT) to a relative path. This separate "
                             "finalizer checks the intact records and does not rerun any solver.",
    }
    encoded = json.dumps(summary, indent=2) + "\n"
    (directory / "summary.json").write_text(encoded)
    Path(__file__).with_name("summary.json").write_text(encoded)
    Path(__file__).with_name("results.json.gz").write_bytes(records_path.read_bytes())
    (directory / "finalize.py").write_bytes(Path(__file__).read_bytes())
    print(encoded, end="")


if __name__ == "__main__":
    main()
