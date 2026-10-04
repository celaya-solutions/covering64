# Document:    Independent Native Fixed-Link Pilot Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Independently recount all bounded native pilot snapshots and operation records."""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("independent_native_gate", HERE / "check.py")
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def main():
    gate = json.loads((HERE / "audit.json").read_text())
    GATE.require(
        GATE.sha(GATE.ROOT / "scripts/fixed_link_profile_heuristic.cpp") == GATE.FROZEN,
        "native source changed",
    )
    GATE.require(
        gate["passed"] is True and gate["checker_sha256"] == GATE.sha(HERE / "check.py"),
        "changed independent gate",
    )
    folder = GATE.RAW / "pilots"
    cases = json.loads((GATE.INPUT / "seeds.json").read_text())["cases"]
    results = json.loads((GATE.INPUT / "results.json").read_text())
    GATE.require([r["name"] for r in results] == [c["name"] for c in cases], "wrong inventory")
    snapshots, operations, records = [], [], []
    for case, result in zip(cases, results, strict=True):
        name = case["name"]
        log = folder / (name + ".log")
        GATE.require(GATE.sha(log) == result["log_sha256"], "log changed")
        GATE.require(not (folder / (name + ".err")).read_bytes(), "native stderr")
        events = list(map(json.loads, log.read_text().splitlines()))
        GATE.require(events[0]["seconds"] == result["requested_seconds"] == 300, "wrong budget")
        GATE.require(events[0]["seed"] == result["seed"] == case["seed"], "wrong seed")
        GATE.require(
            events[0]["workers"] == 1 and events[-1] == result["native_result"],
            "wrong start or finish",
        )
        GATE.require(events[-1]["event"] == "finished", "unfinished native run")
        states = [GATE.recount(p, case) for p in sorted(folder.glob(name + "-*.txt"))]
        moves = GATE.replay(log)
        GATE.require(len(moves) == 15, "missing forced or sampled move")
        GATE.require(
            {e["mode"] for e in moves if e["role"] == "forced_apply"} == {0, 1, 2},
            "missing move mode",
        )
        best = GATE.recount(folder / (name + "-best.txt"), case)
        GATE.require(
            best["sha256"] == result["best_sha256"] and best["holes"] == events[-1]["best_holes"],
            "best differs",
        )
        GATE.require(best["holes"] == min(s["holes"] for s in states), "better saved state")
        GATE.require(result["exit"] == int(bool(best["holes"])), "exit disagrees")
        records.append(
            {
                "name": name,
                "best_holes": best["holes"],
                "seed": case["seed"],
                "seconds": events[-1]["seconds"],
                "snapshot_count": len(states),
                "operation_count": len(moves),
                "log_sha256": GATE.sha(log),
            }
        )
        snapshots.extend(states)
        operations.extend(moves)
    result = {
        "passed": True,
        "checker_sha256": GATE.sha(Path(__file__)),
        "gate_audit_sha256": GATE.sha(HERE / "audit.json"),
        "source_sha256": GATE.FROZEN,
        "snapshot_count": len(snapshots),
        "operation_count": len(operations),
        "pilots": records,
        "snapshots": snapshots,
        "covers": sum(s["holes"] == 0 for s in snapshots),
        "scope": "Independent exact state recount and operation replay. No cover was found; "
        "heuristic exhaustion does not exclude a link or degree profile.",
    }
    (HERE / "pilot-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {k: result[k] for k in ["passed", "snapshot_count", "operation_count", "covers"]}
        )
    )


if __name__ == "__main__":
    main()
