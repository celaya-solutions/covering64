# Document:    Anchor-Pair Lookahead Pilot Best Records and Log Audit
# Version:     v1.2.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      b6d1ab528b82f21ae826c62b5738f474076e0725a623e3d0dbe4bd26c1615a0c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Bind the two independent best records to logs and full saved-state recounts."""

import json
from pathlib import Path

from audit import ROOT, analyze, blocks, require, sha

HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/four-seven-template-native-lookahead-v1.2.0"


def main():
    full = json.loads((HERE / "pilot-audit.json").read_text())
    cases = [
        c
        for c in json.loads((HERE / "seeds.json").read_text())["cases"]
        if (RAW / "pilots" / f"{c['name']}.log").exists()
    ]
    summaries = []
    for case in cases:
        name = case["name"]
        folder = RAW / "pilots"
        events = [json.loads(line) for line in (folder / f"{name}.log").read_text().splitlines()]
        first, last = events[0], events[-1]
        initial = analyze(blocks(folder / f"{name}-initial.txt"), case)
        for field, key in [
            ("initial_holes", "holes"),
            ("initial_score", "score"),
            ("initial_pair_l1", "pair_target_l1"),
            ("initial_nonheavy_excess", "nonheavy_excess"),
        ]:
            require(first[field] == initial[key], "wrong initial log score")
        bests = {}
        for role in ["raw", "score"]:
            path = folder / f"{name}-{role}-best.txt"
            bests[role] = {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha(path),
                **analyze(blocks(path), case),
            }
        require(sha(folder / f"{name}-best.txt") == bests["raw"]["sha256"], "raw alias drift")
        require(
            (last["best_holes"], last["best_raw_score"])
            == (bests["raw"]["holes"], bests["raw"]["score"]),
            "wrong raw best log",
        )
        require(
            (last["best_score"], last["best_score_holes"])
            == (bests["score"]["score"], bests["score"]["holes"]),
            "wrong score best log",
        )
        eligible = [
            s
            for s in full["snapshots"]
            if Path(s["path"]).name.startswith(name + "-")
            and "-control" not in Path(s["path"]).name
        ]
        require(
            min((s["holes"], s["score"]) for s in eligible)
            == (bests["raw"]["holes"], bests["raw"]["score"]),
            "raw saved minimum drift",
        )
        require(
            min((s["score"], s["holes"]) for s in eligible)
            == (bests["score"]["score"], bests["score"]["holes"]),
            "score saved minimum drift",
        )
        for event in events:
            if event.get("event") != "improvement":
                continue
            for role in ["raw", "score"]:
                if not event[f"{role}_improved"]:
                    continue
                suffix = (
                    f"raw-h{event['holes']}-s{event['score']}"
                    if role == "raw"
                    else f"score-s{event['score']}-h{event['holes']}"
                )
                actual = analyze(blocks(folder / f"{name}-{suffix}.txt"), case)
                for key, log_key in [
                    ("holes", "holes"),
                    ("score", "score"),
                    ("pair_target_l1", "pair_l1"),
                    ("nonheavy_excess", "nonheavy_excess"),
                ]:
                    require(actual[key] == event[log_key], "wrong improvement log score")
        mode_names = ["directed_swap", "redistribution", "point_cycle", "whole_template"]
        counters = [
            {
                "mode": mode,
                "attempted": attempted,
                "accepted": accepted,
                "acceptance": accepted / attempted if attempted else None,
            }
            for mode, attempted, accepted in zip(
                mode_names, last.get("attempted", []), last.get("accepted", [])
            )
        ]
        summaries.append(
            {
                "name": name,
                "initial": initial,
                "bests": bests,
                "native_result": last,
                "main_loop_counters": counters,
            }
        )
    result = {
        "checker_sha256": sha(Path(__file__)),
        "pilot_audit_sha256": sha(HERE / "pilot-audit.json"),
        "cases": summaries,
        "scope": "Construction-only results; no exclusion or lower-bound claim.",
    }
    (HERE / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            [
                {
                    "name": c["name"],
                    "raw_holes": c["bests"]["raw"]["holes"],
                    "raw_score": c["bests"]["raw"]["score"],
                    "score_holes": c["bests"]["score"]["holes"],
                    "score": c["bests"]["score"]["score"],
                }
                for c in summaries
            ]
        )
    )


if __name__ == "__main__":
    main()
