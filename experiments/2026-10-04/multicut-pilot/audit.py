# Document:    Full Saved-State Audit of the Single Fourteen-Cut Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      48fc29e77ebb5788f0c5a67b436ea2e5262f96d86a160e28a248fbd19bd4c9cb
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import hashlib
import importlib.util
import itertools
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/multicut-pilot-v1.0.0"
PRIMARY = HERE.parent / "multicut-native-final/audit.py"
SPEC = importlib.util.spec_from_file_location("independent_native_checker", PRIMARY)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    output = RAW / "verification"
    require(not output.exists(), "fresh verification directory required")
    output.mkdir()
    manifest = json.loads((HERE / "manifest.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    source_audit = json.loads((RAW / "inputs/native-audit.json").read_text())
    require(source_audit["checker_sha256"] == sha(PRIMARY), "checker changed")
    require(result["manifest_sha256"] == sha(HERE / "manifest.json"), "manifest changed")
    require(result["stdout_sha256"] == sha(RAW / "stdout.jsonl"), "log changed")
    require(result["stderr_sha256"] == sha(RAW / "stderr.log"), "stderr changed")
    expected_exit = 0 if result["native_finished"]["best_holes"] == 0 else 1
    require(
        result["exit"] == expected_exit and not result["forced_termination"],
        "pilot interrupted or unexpected exit",
    )
    require((RAW / "stderr.log").stat().st_size == 0, "native stderr nonempty")
    require(
        manifest["seed"] == 2026104051
        and manifest["native_seconds"] == 180
        and manifest["processes"] == manifest["workers"] == 1
        and manifest["cut_weight"] == 10,
        "budget changed",
    )
    require(
        manifest["source_sha256"]
        == sha(RAW / "inputs/four_seven_template_multicut_final_heuristic.cpp"),
        "source snapshot changed",
    )
    for key, name in [
        ("binary", "search"),
        ("seed", "seed.txt"),
        ("catalog", "catalog.txt"),
        ("cut", "cut.json"),
        ("gate", "root-gate.json"),
        ("runtime_gate", "runtime-gate.json"),
    ]:
        require(manifest[key + "_sha256"] == sha(RAW / "inputs" / name), "input changed")
    events = [json.loads(line) for line in (RAW / "stdout.jsonl").read_text().splitlines()]
    start = next(e for e in events if e["event"] == "start")
    finished = next(e for e in reversed(events) if e["event"] == "finished")
    require(
        start["seed"] == 2026104051
        and start["seconds"] == 180
        and start["workers"] == 1
        and start["cut_enabled"]
        and start["cut_weight"] == 10,
        "native budget changed",
    )
    states = {}
    for path in sorted(RAW.glob("*.txt")):
        candidate = CHECKER.blocks(path)
        require(len(candidate) == len(set(candidate)) == 64, "distinct 64-block state required")
        require(
            all(len(b) == len(set(b)) == 5 and set(b) <= set(range(1, 17)) for b in candidate),
            "malformed block",
        )
        degrees = Counter(point for block in candidate for point in block)
        require(
            set(degrees) == set(range(1, 17)) and set(degrees.values()) == {20},
            "degree profile differs from regular degree20 family",
        )
        heavy = [b for b in candidate if any(set(a) <= set(b) for a in CHECKER.ANCHORS)]
        require(len(heavy) == 28, "heavy profile count")
        for group, anchor in enumerate(CHECKER.ANCHORS):
            local = [b for b in heavy if set(anchor) <= set(b)]
            outside = Counter(p for b in local for p in set(b) - set(anchor))
            require(
                len(local) == 7
                and outside
                == {p: 2 if p == 4 * group + 4 else 1 for p in range(1, 17) if p not in anchor},
                "heavy outside-point profile",
            )
        pairs = Counter(pair for block in candidate for pair in itertools.combinations(block, 2))
        triples = Counter(t for block in candidate for t in itertools.combinations(block, 3))
        triple_profile = Counter(triples.values())
        triple_profile[0] = 560 - len(triples)
        expected = CHECKER.recount(candidate, "cycle", True, 10)
        detail = json.loads(Path(str(path) + ".lookahead.json").read_text())
        CHECKER.compare(detail, expected)
        checks = {}
        for label, command in [
            ("package", ["uv", "run", "covering64", "verify"]),
            ("standalone", [sys.executable, "scripts/check_cover.py"]),
        ]:
            argv = command + [str(path), "--expected-blocks", "64"]
            checked = subprocess.run(
                argv, cwd=ROOT, capture_output=True, text=True, timeout=30, check=False
            )
            parsed = json.loads(checked.stdout)
            require(checked.returncode in (0, 1) and not checked.stderr, "cover checker error")
            require(parsed["valid"] == (expected["holes"] == 0), "cover validity mismatch")
            require(len(parsed["uncovered"]) == expected["holes"], "cover missing triples mismatch")
            require(parsed["canonical_sha256"] == sha(path), "cover canonical hash mismatch")
            (output / (path.stem + "-" + label + ".json")).write_text(checked.stdout)
            checks[label] = {
                "exit": checked.returncode,
                "valid": parsed["valid"],
                "sha256": sha(output / (path.stem + "-" + label + ".json")),
            }
        states[str(path)] = {
            "sha256": sha(path),
            "sidecar_sha256": sha(Path(str(path) + ".lookahead.json")),
            "holes": expected["holes"],
            "score": expected["score"],
            "base_score": expected["base_score"],
            "cut_lhs": expected["cut_lhs"],
            "cut_violation": expected["cut_violation"],
            "cut_violations": expected["cut_violations"],
            "all14cuts_pass": expected["cut_violation"] == 0,
            "cut_penalty": expected["cut_penalty"],
            "unsupported_count": expected["unsupported_count"],
            "admissible_count": expected["admissible_count"],
            "heavy_excess": expected["heavy_excess"],
            "point_degrees": [degrees[p] for p in range(1, 17)],
            "pair_count_profile": dict(sorted(Counter(pairs.values()).items())),
            "triple_count_profile": dict(sorted(triple_profile.items())),
            "heavy_outside_profiles_passed": True,
            "checks": checks,
        }
    operations = 0
    for event in events:
        if event["event"] != "operation":
            continue
        before, after = CHECKER.blocks(Path(event["before"])), CHECKER.blocks(Path(event["after"]))
        require(
            set(after)
            == (set(before) - set(map(tuple, event["removed"]))) | set(map(tuple, event["added"])),
            "operation inventory",
        )
        for side in ["before", "after"]:
            record = states[event[side]]
            require(
                event["holes_" + side] == record["holes"]
                and event["score_" + side] == record["score"],
                "operation score",
            )
        if event["mode"] < 3:
            require(
                states[event["before"]]["cut_lhs"] == states[event["after"]]["cut_lhs"],
                "ordinary operation changed heavy score",
            )
        operations += 1
    for mode in range(4):
        require(
            states[str(RAW / f"cycle-control{mode}-before.txt")]["sha256"]
            == states[str(RAW / f"cycle-control{mode}-rollback.txt")]["sha256"],
            "rollback state mismatch",
        )
    require(str(RAW / "cycle-final.txt") in states, "terminal state absent")
    raw_best, score_best = (
        states[str(RAW / "cycle-raw-best.txt")],
        states[str(RAW / "cycle-score-best.txt")],
    )
    require(
        (raw_best["holes"], raw_best["score"])
        == min((s["holes"], s["score"]) for s in states.values()),
        "raw best mismatch",
    )
    require(
        (score_best["score"], score_best["holes"])
        == min((s["score"], s["holes"]) for s in states.values()),
        "score best mismatch",
    )
    require(
        finished["best_holes"] == raw_best["holes"]
        and finished["best_raw_score"] == raw_best["score"]
        and finished["best_score"] == score_best["score"]
        and finished["best_score_holes"] == score_best["holes"],
        "native best summaries",
    )
    sample_path = RAW / "cycle-raw-best.txt"
    expected = CHECKER.recount(CHECKER.blocks(sample_path), "cycle", True, 10)
    detail = json.loads(Path(str(sample_path) + ".lookahead.json").read_text())
    controls = []
    for field in [
        "holes",
        "score",
        "base_score",
        "cut_lhs",
        "cut_rhs",
        "cut_violations",
        "cut_weight",
        "cut_count",
        "cut_violation",
        "cut_penalty",
        "cut_denominator",
        "unsupported_count",
        "admissible_count",
    ]:
        damaged = copy.deepcopy(detail)
        if isinstance(damaged[field], list):
            damaged[field][0] += 1
        else:
            damaged[field] += 1
        try:
            CHECKER.compare(damaged, expected)
        except ValueError:
            controls.append(field)
        else:
            raise AssertionError("damaged metric accepted")
    for name in ["cycle-raw-best.txt", "cycle-score-best.txt", "cycle-best.txt", "cycle-final.txt"]:
        (HERE / name).write_bytes((RAW / name).read_bytes())
        (HERE / (name + ".lookahead.json")).write_bytes(
            (RAW / (name + ".lookahead.json")).read_bytes()
        )
    receipt = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "source_checker_sha256": sha(PRIMARY),
        "source_sha256": manifest["source_sha256"],
        "manifest_sha256": sha(HERE / "manifest.json"),
        "result_sha256": sha(HERE / "result.json"),
        "states": len(states),
        "operations": operations,
        "both_cover_checkers_on_every_saved_state": True,
        "complete_lookahead_sets_checked": True,
        "damaged_fields_rejected": len(controls),
        "damage_controls": controls,
        "raw_best": raw_best,
        "score_best": score_best,
        "terminal": states[str(RAW / "cycle-final.txt")],
        "snapshots": states,
        "scope": "Construction-only pilot. Positive hole counts are not covering witnesses; "
        "the fourteen cuts are only a regular-template score guide.",
    }
    (HERE / "audit.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (output / "audit.json").write_bytes((HERE / "audit.json").read_bytes())
    print(json.dumps({k: v for k, v in receipt.items() if k != "snapshots"}))


if __name__ == "__main__":
    main()
