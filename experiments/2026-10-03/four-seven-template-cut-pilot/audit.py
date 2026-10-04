# Document:    Full Saved-State Audit of the Single Heavy-Cut Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      7f4e3e9d54d94a59071f006465be4671fa01cdb0d8f5a12757bb7c71320b62bf
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/four-seven-template-cut-pilot-v1.0.0"
PRIMARY = HERE.parent / "four-seven-template-cut/audit.py"
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
        manifest["seed"] == 2026104722
        and manifest["native_seconds"] == 300
        and manifest["processes"] == manifest["workers"] == 1,
        "budget changed",
    )
    require(
        manifest["source_sha256"] == sha(RAW / "inputs/four_seven_template_cut_heuristic.cpp"),
        "source snapshot changed",
    )
    for key, name in [
        ("binary", "search"),
        ("seed", "seed.txt"),
        ("catalog", "catalog.txt"),
        ("cut", "cut.json"),
        ("gate", "root-gate.json"),
    ]:
        require(manifest[key + "_sha256"] == sha(RAW / "inputs" / name), "input changed")
    events = [json.loads(line) for line in (RAW / "stdout.jsonl").read_text().splitlines()]
    start = next(e for e in events if e["event"] == "start")
    finished = next(e for e in reversed(events) if e["event"] == "finished")
    require(
        start["seed"] == 2026104722 and start["seconds"] == 300 and start["workers"] == 1,
        "native budget changed",
    )
    states = {}
    for path in sorted(RAW.glob("*.txt")):
        candidate = CHECKER.blocks(path)
        expected = CHECKER.recount(candidate, "cycle", True)
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
            "cut_penalty": expected["cut_penalty"],
            "unsupported_count": expected["unsupported_count"],
            "admissible_count": expected["admissible_count"],
            "heavy_excess": expected["heavy_excess"],
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
    expected = CHECKER.recount(CHECKER.blocks(sample_path), "cycle", True)
    detail = json.loads(Path(str(sample_path) + ".lookahead.json").read_text())
    controls = []
    for field in [
        "holes",
        "score",
        "base_score",
        "cut_lhs",
        "cut_rhs",
        "cut_violation",
        "cut_penalty",
        "cut_denominator",
        "unsupported_count",
        "admissible_count",
    ]:
        damaged = copy.deepcopy(detail)
        damaged[field] += 1
        try:
            CHECKER.compare(damaged, expected)
        except ValueError:
            controls.append(field)
        else:
            raise AssertionError("damaged metric accepted")
    for name in ["cycle-raw-best.txt", "cycle-score-best.txt", "cycle-best.txt"]:
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
        "snapshots": states,
        "scope": "Construction-only pilot. Positive hole counts are not covering witnesses; "
        "the labeled cut is only a regular-template score guide.",
    }
    (HERE / "audit.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (output / "audit.json").write_bytes((HERE / "audit.json").read_bytes())
    print(json.dumps({k: v for k, v in receipt.items() if k != "snapshots"}))


if __name__ == "__main__":
    main()
