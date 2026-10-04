#!/usr/bin/env python3
# Document:    Exact Larger Neighborhood Cut Intersection
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Read a finite campaign snapshot and replay every support plane exactly."""

import json
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

from basis import INF, digest, rebuild
from bundle_check import rational, sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
RAW = ROOT / "experiments/scratch/lp-guided-larger-intersection-20261004"
NEAREST = ROOT / "experiments/scratch/nearest-heavy-master-20261004"


def main():
    output = HERE / "cut-intersection.json"
    assert not output.exists() and not RAW.exists()
    manifest_path = DAY / "nearest-heavy-master/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    paths = {}

    def read(path, expected=None):
        assert expected is None or sha(path) == expected
        paths[str(path.relative_to(ROOT))] = sha(path)
        return json.loads(path.read_text())

    base_path = ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/cut-bundle.json"
    base = read(base_path, manifest["input_files"][str(base_path.relative_to(ROOT))])
    cuts = [(f"initial/base/{cut['id']}", cut) for cut in base["cuts"]]
    for folder, expected_count, pattern in (
        ("lazy-heavy-master-independent", 10, "learned-cut-"),
        ("lazy-heavy-master-continuation", 100, "/learned-cut.json"),
    ):
        gate_path = DAY / folder / "postcheck.json"
        gate = read(gate_path, manifest["input_files"][str(gate_path.relative_to(ROOT))])
        assert gate["passed"] and gate["checked_new_cuts"] == expected_count
        matching = sorted((p, h) for p, h in gate["receipts"].items() if pattern in p)
        assert len(matching) == expected_count
        for name, expected in matching:
            cuts.append(("initial/" + name, read(ROOT / name, expected)))
    sweep_path = DAY / "lp-guided-sweep-cuts/bundle.json"
    sweep = read(sweep_path, manifest["input_files"][str(sweep_path.relative_to(ROOT))])
    cuts += [("initial/" + cut["id"], cut) for cut in sweep["cuts"]]
    best_path = DAY / "lp-guided-best-lp/cut.json"
    cuts.append(("initial/best-baseline", read(
        best_path, manifest["input_files"][str(best_path.relative_to(ROOT))])))
    assert len(cuts) == manifest["cut_count"] == 238
    snapshot_path = DAY / "nearest-heavy-master/result.json"
    completed = snapshot_path.exists()
    if not completed:
        snapshot_path = NEAREST / "steps.json"
    snapshot_bytes = snapshot_path.read_bytes()
    snapshot = json.loads(snapshot_bytes)
    records = snapshot["records"] if completed else snapshot
    for record in records:
        if "learned_cut_sha256" in record:
            path = NEAREST / f"step-{record['step']:03d}/learned-cut.json"
            cuts.append((f"nearest/{record['step']:03d}", read(path, record["learned_cut_sha256"])))

    blocks, _, ordinary, heavy, rows = rebuild()
    heavy_global_ids = [blocks.index(block) for block in heavy]
    assert heavy_global_ids == base["heavy_global_ids"] == sweep["heavy_global_ids"]
    assert [blocks.index(block) for block in ordinary] == base["ordinary_global_ids"]
    support_o = [[r for r, row in enumerate(rows) if i in row[0]] for i in range(1200)]
    support_h = [[r for r, row in enumerate(rows) if i in row[1]] for i in range(276)]
    checked = []
    for name, cut in cuts:
        if "dual" in cut:
            dual = cut["dual"]
        elif "certificate_path" in cut:
            dual = read(ROOT / cut["certificate_path"], cut["certificate_sha256"])
        else:
            dual = read(ROOT / cut["dual_path"], cut["dual_sha256"])
        denominator = cut["denominator"]
        assert denominator == dual["denominator"] and denominator in (1000, 1000000)
        weights, seen = [0] * 697, set()
        for index, value in dual["weights"]:
            assert index not in seen and 0 <= index < 697
            assert type(value) is int and 0 < abs(value) <= denominator
            assert value >= 0 or rows[index][3] != INF
            weights[index] = value
            seen.add(index)
        coefficients_o = [sum(weights[r] for r in support) for support in support_o]
        coefficients_h = [sum(weights[r] for r in support) for support in support_h]
        constant = sum(w * (rows[r][2] if w > 0 else rows[r][3])
                       for r, w in enumerate(weights) if w)
        box = sum(max(0, value) for value in coefficients_o)
        assert coefficients_h == cut["coefficients"] and constant - box == cut["rhs"]
        if "ordinary_coefficients" in cut:
            assert coefficients_o == cut["ordinary_coefficients"]
        checked.append({"id": name, "denominator": denominator, "rhs": cut["rhs"],
                        "coefficients": coefficients_h, "maximum_weight": max(map(abs, weights))})
    positions = {global_id: index for index, global_id in enumerate(heavy_global_ids)}
    baseline = {positions[i] for i in manifest["baseline_heavy_global_ids"]}
    candidates = []
    for kind in ("proper-three", "paired-two"):
        raw_path = ROOT / f"experiments/scratch/lp-guided-larger-moves-20261004/{kind}.json"
        entries = read(raw_path)
        candidates.extend((kind, entry) for entry in entries if entry["lower_bound_numerator"] == 0)
    assert len(candidates) == 27
    reports = []
    for kind, entry in candidates:
        selected = baseline - set(entry["removed_heavy_ids"]) | set(entry["added_heavy_ids"])
        assert len(selected) == 28
        assert digest(sorted(heavy[i] for i in selected)) == entry["state_sha256"]
        bounds = [(Fraction(cut["rhs"] - sum(cut["coefficients"][i] for i in selected),
                            cut["denominator"]), cut["id"]) for cut in checked]
        initial = max(bounds[:238])
        learned = max(bounds[238:]) if len(bounds) > 238 else (Fraction(0), None)
        positive = [name for value, name in bounds if value > 0]
        global_ids = [heavy_global_ids[i] for i in sorted(selected)]
        matching = [record["step"] for record in records
                    if record.get("heavy_global_ids") == global_ids]
        reports.append({"kind": kind, "state_sha256": entry["state_sha256"],
                        "heavy_global_ids": [heavy_global_ids[i] for i in sorted(selected)],
                        "initial_maximum_signed_bound": rational(initial[0]),
                        "initial_maximizing_cut": initial[1],
                        "learned_maximum_signed_bound": rational(learned[0]),
                        "learned_maximizing_cut": learned[1],
                        "strictly_violated_cuts": positive, "matching_nearest_steps": matching,
                        "survives_initial": initial[0] <= 0,
                        "survives_all_snapshot_cuts": not positive})
    RAW.mkdir()
    (RAW / "nearest-snapshot.json").write_bytes(snapshot_bytes)
    (RAW / "checked-planes.json").write_text(json.dumps(checked, indent=2) + "\n")
    report = {"passed": True, "solver_calls": 0,
              "snapshot_utc": datetime.now(timezone.utc).isoformat(),
              "nearest_completed": completed, "nearest_records": len(records),
              "initial_cuts": 238, "new_cuts": len(checked) - 238,
              "all_plane_signed_sums_and_norm_bounds_rechecked": True,
              "candidates": len(reports),
              "survives_initial": sum(row["survives_initial"] for row in reports),
              "survives_all_snapshot_cuts": sum(row["survives_all_snapshot_cuts"]
                                                for row in reports),
              "already_evaluated": sum(bool(row["matching_nearest_steps"]) for row in reports),
              "checker_sha256": sha(__file__), "manifest_sha256": sha(manifest_path),
              "nearest_snapshot_sha256": sha(RAW / "nearest-snapshot.json"),
              "checked_planes_sha256": sha(RAW / "checked-planes.json"),
              "inputs": paths, "records": reports,
              "scope": "Exact cut intersection for the 27 zero-envelope finite neighbors only."}
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("inputs", "records")}, indent=2))


if __name__ == "__main__":
    main()
