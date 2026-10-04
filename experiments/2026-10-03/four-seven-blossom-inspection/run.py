"""Document:    Saved Heavy-Link Blossom Violation Inspection
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      d8a813ecf94f51262d6e753cc0aba59a4120b8298635688280a737169486a989
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
"""

import gzip
import hashlib
import itertools
import json
import math
import platform
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PRIMALS = ROOT / "experiments/scratch/four-seven-lp-primal-inspection-20261003"
ORIGINAL = ROOT / "experiments/scratch/four-seven-link-lp-full/results.json.gz"
OUTPUT = ROOT / "experiments/scratch/four-seven-blossom-inspection-v1.0.0"
TOLERANCE = 1e-7
ANCHORS = ((1, 2, 3), (5, 6, 7), (9, 10, 11), (13, 14, 15))
HUBS = (4, 8, 12, 16)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUTPUT.exists():
        raise ValueError("output archive must be new")
    OUTPUT.mkdir()
    blocks = list(itertools.combinations(range(1, 17), 5))
    block_ids = {block: index for index, block in enumerate(blocks)}
    full_results = json.loads(gzip.decompress(ORIGINAL.read_bytes()))
    survivors = {row["id"]: row for row in full_results if not row["proves_infeasible"]}
    assert len(survivors) == 158
    link_rows = []
    for group, (anchor, hub) in enumerate(zip(ANCHORS, HUBS)):
        outside = sorted(set(range(1, 17)) - set(anchor))
        edges = list(itertools.combinations(outside, 2))
        ids = [block_ids[tuple(sorted((*anchor, *edge)))] for edge in edges]
        degree_matrix = np.asarray([[int(point in edge) for edge in edges]
                                    for point in outside], dtype=float)
        targets = np.asarray([2 if point == hub else 1 for point in outside])
        subsets = [subset for size in range(1, 7)
                   for subset in itertools.combinations(outside, size)
                   if (size + int(hub in subset)) % 2]
        assert len(subsets) == 2048
        masks = [set(subset) for subset in subsets]
        matrix = np.asarray([[int(left in subset and right in subset)
                              for left, right in edges] for subset in masks], dtype=float)
        bounds = np.asarray([(len(subset) + int(hub in subset)) // 2
                             for subset in subsets], dtype=float)
        link_rows.append((group, hub, outside, edges, ids, degree_matrix, targets,
                          subsets, matrix, bounds))
    records = []
    frequency = Counter()
    strongest = {}
    max_residual = 0.0
    for rep_id, original in sorted(survivors.items()):
        directory = PRIMALS / rep_id
        primal_path = directory / "primal.json.gz"
        result = json.loads((directory / "result.json").read_text())
        primal = json.loads(gzip.decompress(primal_path.read_bytes()))
        assert sha(primal_path) == result["primal_sha256"]
        assert primal["id"] == rep_id and primal["case"] == original["case"]
        assert primal["fixed_ids"] == original["fixed_ids"]
        values = np.asarray(primal["values"], dtype=float)
        assert len(values) == primal["width"] == 4768
        assert all(math.isfinite(value) for value in values)
        assert min(values) >= -TOLERANCE and max(values) <= 1 + TOLERANCE
        record = {"id": rep_id, "case": primal["case"],
                  "primal_sha256": sha(primal_path), "groups": []}
        for (group, hub, outside, edges, ids, degree_matrix, targets,
             subsets, matrix, bounds) in link_rows:
            edge_values = values[ids]
            residual = float(max(abs(degree_matrix @ edge_values - targets)))
            assert residual < TOLERANCE
            max_residual = max(max_residual, residual)
            excesses = matrix @ edge_values - bounds
            violations = []
            for index in np.flatnonzero(excesses > TOLERANCE):
                subset = subsets[index]
                inside = set(subset)
                # Independent direct arithmetic and complement identity checks.
                direct = math.fsum(float(value) for edge, value in zip(edges, edge_values)
                                   if set(edge) <= inside) - bounds[index]
                complement = set(outside) - inside
                complement_bound = (len(complement) + int(hub in complement)) // 2
                complement_excess = math.fsum(
                    float(value) for edge, value in zip(edges, edge_values)
                    if set(edge) <= complement) - complement_bound
                assert abs(direct - excesses[index]) < TOLERANCE
                assert abs(direct - complement_excess) < TOLERANCE
                key = (primal["case"], group, subset)
                frequency[key] += 1
                strongest[key] = max(strongest.get(key, 0.0), direct)
                violations.append({"subset": subset, "upper": int(bounds[index]),
                                   "excess": float(direct)})
            record["groups"].append({"group": group, "anchor": ANCHORS[group],
                                     "hub": hub, "degree_residual": residual,
                                     "count": len(violations),
                                     "maximum_excess": max((r["excess"] for r in violations),
                                                           default=0.0),
                                     "violations": violations})
        record["violation_count"] = sum(row["count"] for row in record["groups"])
        record["maximum_excess"] = max(row["maximum_excess"] for row in record["groups"])
        records.append(record)
    archive = OUTPUT / "violations.json.gz"
    archive.write_bytes(gzip.compress((json.dumps(records) + "\n").encode(), mtime=0))
    (OUTPUT / "run.py").write_bytes(Path(__file__).read_bytes())
    ranked_cuts = [{"case": case, "group": group, "subset": subset,
                    "primal_count": count, "maximum_excess": strongest[(case, group, subset)]}
                   for (case, group, subset), count in frequency.most_common()]
    summary = {
        "scope": "Numerical violations in saved fractional LP vectors, not integer exclusions.",
        "source_sha256": sha(Path(__file__)), "original_results_sha256": sha(ORIGINAL),
        "primals_directory": str(PRIMALS.relative_to(ROOT)),
        "archive": str(archive.relative_to(ROOT)), "archive_sha256": sha(archive),
        "python_version": platform.python_version(), "numpy_version": np.__version__,
        "tolerance": TOLERANCE, "records": len(records),
        "canonical_subsets_per_group": 2048, "maximum_degree_residual": max_residual,
        "total_violations": sum(row["violation_count"] for row in records),
        "distinct_case_group_cuts_violated": len(frequency),
        "cases_with_violations": sum(row["violation_count"] > 0 for row in records),
        "maximum_excess": max(row["maximum_excess"] for row in records),
        "by_case": {}, "top_cuts": ranked_cuts[:50],
        "ranking": [{key: row[key] for key in ("id", "case", "violation_count", "maximum_excess")}
                    for row in sorted(records, key=lambda row: (-row["maximum_excess"],
                                                               -row["violation_count"],
                                                               row["id"]))],
    }
    for case in ("cycle", "matching"):
        selected = [row for row in records if row["case"] == case]
        summary["by_case"][case] = {
            "records": len(selected),
            "with_violations": sum(row["violation_count"] > 0 for row in selected),
            "total_violations": sum(row["violation_count"] for row in selected),
            "per_group": [{"group": group,
                           "records_with_violations": sum(row["groups"][group]["count"] > 0
                                                          for row in selected),
                           "total_violations": sum(row["groups"][group]["count"]
                                                   for row in selected),
                           "maximum_excess": max(row["groups"][group]["maximum_excess"]
                                                 for row in selected)} for group in range(4)],
        }
    (OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    Path(__file__).with_name("summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({key: summary[key] for key in (
        "records", "total_violations", "distinct_case_group_cuts_violated",
        "cases_with_violations", "maximum_excess", "maximum_degree_residual", "by_case")},
        indent=2))


if __name__ == "__main__":
    main()
