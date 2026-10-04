# Document:    Independent Native Core Escape Run Postcheck
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      b9a7425b787066659b8175af52fcfb02c8559939ed0dd89c1cac97cb6e69940b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Audit frozen native traces and every saved64-family without construction calls."""

import importlib.util
import itertools
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGET = ROOT / "experiments/2026-10-04/native-core-cap-escape-v2"
spec = importlib.util.spec_from_file_location("independent_native_gate", HERE / "check.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def main():
    gate = json.loads((HERE / "gate.json").read_text())
    manifest = json.loads((TARGET / "manifest.json").read_text())
    producer = json.loads((TARGET / "result.json").read_text())
    assert gate["passed"]
    assert audit.sha(HERE / "check.py") == gate["check_sha256"]
    assert audit.sha(HERE / "control.cpp") == gate["control_sha256"]
    assert audit.sha(TARGET / "manifest.json") == gate["manifest_sha256"]
    assert producer["manifest_sha256"] == gate["manifest_sha256"]
    assert producer["gate_sha256"] == audit.sha(HERE / "gate.json")
    assert producer["binary_sha256"] == gate["binary_sha256"]
    assert not producer["global_lower_bound_claim"]
    for relative, expected in (manifest["input_files"] | manifest["raw_files"]).items():
        assert audit.sha(ROOT / relative) == expected
    binary = ROOT / manifest["binary_path"]
    assert audit.sha(binary) == gate["binary_sha256"]
    raw = binary.parent
    start = json.loads((raw / "start.json").read_text())
    assert start["manifest_sha256"] == gate["manifest_sha256"]
    assert start["gate_sha256"] == audit.sha(HERE / "gate.json") and not start["relaunch"]
    for name in [
        "search.cpp",
        "heuristic_search.cpp",
        "cores.hpp",
        "control.cpp",
        "prepare.py",
        "run.py",
        "manifest.json",
    ]:
        assert audit.sha(raw / "frozen-sources" / name) == audit.sha(TARGET / name)
    assert audit.sha(raw / "frozen-sources/gate.json") == audit.sha(HERE / "gate.json")
    checked = []
    prior_end = None
    for index, case in enumerate(producer["cases"]):
        seed = manifest["budget"]["seeds"][index]
        assert case["seed"] == seed
        assert case["validation_error"] is None
        assert case["exit_code"] in (0, 1)
        watchdog = case["watchdog"]
        assert watchdog == {
            "deadline_seconds": 75,
            "fired": False,
            "terminate_sent": False,
            "kill_sent": False,
            "relaunch": False,
        }
        started, ended = map(datetime.fromisoformat, [case["started_utc"], case["ended_utc"]])
        assert started <= ended
        if prior_end is not None:
            assert prior_end <= started
        prior_end = ended
        assert 0 <= case["wall_seconds"] < 75
        directory = TARGET / f"seed-{seed}"
        assert case["command"] == [
            str(binary),
            str(ROOT / manifest["hint_path"]),
            str(seed),
            "60",
            str(directory / "search"),
        ]
        for relative, expected in case["raw_files"].items():
            assert audit.sha(ROOT / relative) == expected
        stdout = (raw / f"seed-{seed}-stdout.jsonl").read_text()
        assert not (raw / f"seed-{seed}-stderr.txt").read_text()
        events = [json.loads(line) for line in stdout.splitlines()]
        assert events[0] == {"event": "start", "seed": seed, "budget": 60}
        assert all(
            row["event"]
            in {"start", "improvement", "progress", "finished", "interrupted", "cover_found"}
            for row in events
        )
        improvements = [row for row in events if row["event"] == "improvement"]
        scores = [row["missing"] for row in improvements]
        assert scores[0] == 10 and all(a > b for a, b in zip(scores, scores[1:]))
        current_event = events[-1]
        assert current_event["event"] == ("cover_found" if case["exit_code"] == 0 else "finished")
        for key in ["iterations", "restarts", "core_rejections"]:
            assert type(current_event[key]) is int and current_event[key] >= 0
        assert current_event["core_rejections"] <= current_event["iterations"]
        assert 0 <= current_event["seconds"] <= case["wall_seconds"] + 1
        if case["exit_code"] == 1:
            assert 60 <= current_event["seconds"]
        snapshots = []
        found_paths = set()
        for snapshot in case["snapshots"]:
            path = ROOT / snapshot["path"]
            assert path.parent == directory and path not in found_paths
            found_paths.add(path)
            independent = audit.check_family(path, gate["core_rows"])
            assert independent["sha256"] == snapshot["sha256"]
            assert independent["holes"] == snapshot["holes"]
            assert independent["core_overlaps"] == snapshot["core_overlaps"]
            assert all(overlap <= 55 for overlap in independent["core_overlaps"])
            forbidden = bool(independent["forbidden_partitions"])
            assert forbidden == bool(snapshot["global_profile_obstructions"])
            assert snapshot["eligible_record"] == (not forbidden)
            assert snapshot["role"] in {"eligible_improvement", "final_best", "final_current"}
            if snapshot["role"] != "final_current":
                assert not forbidden
            native = json.loads(audit.run([str(binary), "--profile", str(path)]).stdout)
            assert native == {
                "missing": independent["holes"],
                "forbidden": forbidden,
                "core_overlaps": independent["core_overlaps"],
                "caps_pass": True,
            }
            blocks = audit.family(path)
            points = Counter(p for block in blocks for p in block)
            pairs = Counter(pair for block in blocks for pair in itertools.combinations(block, 2))
            independent["role"] = snapshot["role"]
            independent["minimum_point_degree"] = min(points.get(p, 0) for p in range(1, 17))
            independent["minimum_pair_count"] = min(
                pairs.get(pair, 0) for pair in itertools.combinations(range(1, 17), 2)
            )
            independent["pairs_below_five"] = [
                list(pair)
                for pair in itertools.combinations(range(1, 17), 2)
                if pairs.get(pair, 0) < 5
            ]
            snapshots.append(independent)
        assert found_paths == set(directory.glob("*.txt"))
        (best,) = [row for row in snapshots if row["role"] == "final_best"]
        (current,) = [row for row in snapshots if row["role"] == "final_current"]
        recorded = [row for row in snapshots if row["role"] == "eligible_improvement"]
        assert sorted(row["holes"] for row in recorded) == sorted(scores)
        (last_record,) = [row for row in recorded if row["holes"] == scores[-1]]
        assert best["canonical_sha256"] == last_record["canonical_sha256"]
        assert best["holes"] == current_event["best"] == case["best_eligible_holes"]
        assert current["holes"] == current_event["current_missing"]
        assert current["core_overlaps"] == current_event["final_core_overlaps"]
        assert best["core_overlaps"] == current_event["best_core_overlaps"]
        assert bool(current["forbidden_partitions"]) == current_event["final_profile_forbidden"]
        if case["exit_code"] == 0:
            assert best["holes"] == current["holes"] == 0
        checked.append(
            {
                "seed": seed,
                "scores": scores,
                "status": current_event,
                "wall_seconds": case["wall_seconds"],
                "watchdog": watchdog,
                "snapshots": snapshots,
            }
        )
    assert producer["optimizer_calls"] == len(checked)
    assert len(checked) == 2 or (len(checked) == 1 and checked[0]["status"]["best"] == 0)
    all_snapshots = [row for case in checked for row in case["snapshots"]]
    result = {
        "passed": True,
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "check_sha256": audit.sha(__file__),
        "gate_sha256": audit.sha(HERE / "gate.json"),
        "manifest_sha256": audit.sha(TARGET / "manifest.json"),
        "result_sha256": audit.sha(TARGET / "result.json"),
        "construction_calls_in_audit": 0,
        "producer_optimizer_calls": len(checked),
        "saved_or_final_records": len(all_snapshots),
        "distinct_families": len({row["canonical_sha256"] for row in all_snapshots}),
        "best_eligible_holes": min(case["status"]["best"] for case in checked),
        "cases": checked,
        "global_lower_bound_claim": False,
    }
    (HERE / "postcheck.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "cases"}))


if __name__ == "__main__":
    main()
