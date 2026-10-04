# Document:    Exact Certificate Retries for Seven Unresolved Hub Subcases
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      d3cf6e435e2d75307a146e9ecdc322b85edf090068e8534773993f182a86bd04
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Retry only inconclusive cases; preserve the original campaign unchanged."""

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from four_seven_link_lp import exact_certificate, solve_lp  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output directory must be new")
    args.output.mkdir(parents=True)
    original = ROOT / "experiments/scratch/four-seven-hub-campaign-v1.0.0"
    summary_path = Path(__file__).with_name("campaign-summary.json")
    summary = json.loads(summary_path.read_text())
    if len(summary["inconclusive"]) != 7:
        raise ValueError("expected exactly the seven saved unresolved cases")
    metadata = {"source_sha256": sha(Path(__file__)), "summary_sha256": sha(summary_path),
                "solver_helper_sha256": sha(ROOT / "scripts/four_seven_link_lp.py"),
                "seconds_per_phase": 60, "soft_rows": "seven fixed-link equalities only",
                "scope": "Same exact models; longer certificate search. No original file changed."}
    (args.output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    (args.output / "four_seven_link_lp.py").write_bytes(
        (ROOT / "scripts/four_seven_link_lp.py").read_bytes())
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    results = []
    for item in summary["inconclusive"]:
        m4, z = item["hub_case"]
        child = original / f"m4-{m4}-z-{z}"
        old_results = json.loads(gzip.decompress((child / "results.json.gz").read_bytes()))
        old = next(row for row in old_results if row["id"] == item["id"])
        row_path = child / f"{old['case']}-rows.json.gz"
        payload = json.loads(gzip.decompress(row_path.read_bytes()))
        base = payload["rows"]
        rows = base + [((index,), (1,), 1, 1) for index in old["fixed_ids"]]
        phase = solve_lp(rows, payload["width"], 60, phase_one=True,
                         soft_rows=range(len(base), len(rows)))
        result = {**item, "case": old["case"], "fixed_ids": old["fixed_ids"],
                  "row_archive": str(row_path.relative_to(ROOT)),
                  "row_archive_sha256": sha(row_path), "phase": phase,
                  "checked_rows": len(rows), "checked_columns": payload["width"],
                  "proves_infeasible": False, "certificates": []}
        if "weights" in phase:
            for denominator in (1_000_000, 100_000_000, 10_000_000_000):
                certificate = exact_certificate(rows, payload["width"], phase["weights"],
                                                denominator)
                result["certificates"].append(certificate)
                if certificate["proves_infeasible"]:
                    result["proves_infeasible"] = True
                    break
        results.append(result)
        (args.output / "results.json.gz").write_bytes(gzip.compress(
            (json.dumps(results, indent=2, allow_nan=False) + "\n").encode(), mtime=0))
        print(json.dumps({"id": item["id"], "hub_case": item["hub_case"],
                          "phase_status": phase["status"],
                          "pending_certificate": result["proves_infeasible"]}), flush=True)


if __name__ == "__main__":
    main()
