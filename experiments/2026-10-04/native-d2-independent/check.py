# Document:    Independent Native D2 Pilot Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      3534508e2c341d929bb3e35c0bfe4f9c8c052a009618c0edb08e4c810ee80ade
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import hashlib
import itertools
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "native-pair-two-penalty"
RAW = ROOT / "experiments/scratch/native-d2-independent-20261004"
EXPECTED_MANIFEST = "fc6db0facd6e144fee319e33da869c9e9e013db2d4b92f12787700be5438b11e"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
RANK = {block: index for index, block in enumerate(BLOCKS)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def recount(path, cores):
    rows = [
        tuple(map(int, line.split()))
        for line in Path(path).read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert len(rows) == len(set(rows)) == 64
    assert all(len(row) == len(set(row)) == 5 and tuple(sorted(row)) in RANK for row in rows)
    rows = [tuple(sorted(row)) for row in rows]
    triples = Counter(t for row in rows for t in itertools.combinations(row, 3))
    pairs = Counter(p for row in rows for p in itertools.combinations(row, 2))
    quads = Counter(q for row in rows for q in itertools.combinations(row, 4))
    d2max = d2sum = d3 = d4 = 0
    for pair in itertools.combinations(range(1, 17), 2):
        values = [triples[tuple(sorted((*pair, x)))] for x in range(1, 17) if x not in pair]
        assert sum(values) == 3 * pairs[pair]
        deficits = [
            max(0, 12 - 3 * pairs[pair] + a + b) for a, b in itertools.combinations(values, 2)
        ]
        d2max += max(deficits)
        d2sum += sum(deficits)
        d3 += sum(max(0, 13 - 3 * pairs[pair] + value) for value in values)
        for a, b in itertools.combinations((x for x in range(1, 17) if x not in pair), 2):
            d4 += max(0, 12 - 3 * pairs[pair] + 2 * quads[tuple(sorted((*pair, a, b)))])
    heavy = [triple for triple, count in triples.items() if count >= 6]
    forbidden = any(
        len(set().union(*map(set, selection))) == 15
        and sum(triples[t] >= 7 for t in selection) >= 2
        for selection in itertools.combinations(heavy, 5)
    )
    holes = 560 - len(triples)
    selected = {RANK[row] for row in rows}
    return {
        "holes": holes,
        "D2max": d2max,
        "D2sum": d2sum,
        "D3": d3,
        "D4": d4,
        "energy": 20 * d2max + holes,
        "pair_min": min(pairs[p] for p in itertools.combinations(range(1, 17), 2)),
        "forbidden": forbidden,
        "core_overlaps": [len(selected & set(core)) for core in cores],
    }


def main():
    manifest = read(SOURCE / "manifest.json")
    assert sha(SOURCE / "manifest.json") == EXPECTED_MANIFEST
    for relative, digest in (manifest["input_files"] | manifest["raw_files"]).items():
        assert sha(ROOT / relative) == digest, relative
    assert sha(SOURCE / "search.cpp") == manifest["source_sha256"]
    assert sha(SOURCE / "run.py") == manifest["runner_sha256"]
    assert sha(ROOT / manifest["binary_path"]) == manifest["binary_sha256"]
    previous = HERE.parent / "native-pair-penalty"
    assert sha(SOURCE / "native_pair_base.cpp") == sha(previous / "search.cpp")
    for name in ("native_core_base.cpp", "heuristic_search.cpp", "cores.hpp"):
        assert sha(SOURCE / name) == sha(previous / name)
    assert manifest["core_rows"][:3] == read(previous / "manifest.json")["core_rows"]
    fourth = read(HERE.parent / "fourth-core-independent/audit.json")
    assert manifest["core_rows"][3] == fourth["core_global_ids"]
    assert manifest["core_upper_bound"] == 55
    assert manifest["budget"] == {
        "max_runs": 2,
        "seconds_per_run": 60,
        "seeds": [2026104501, 2026104502],
        "stop_after_first_D2max_zero": True,
        "unused_budget_reallocated": False,
        "additional_budget_on_phase_transition": 0,
        "watchdog_seconds": 75,
        "termination_grace_seconds": 5,
        "simultaneous_processes": 1,
        "relaunch": False,
    }
    assert manifest["energy"] == "20*D2max+H"
    assert manifest["metropolis_delta"] == "integer energy change divided by20"
    assert manifest["best_restart_key"] == ["D2max", "H"]
    assert manifest["phase_count"] == 1 and manifest["stop_entire_pilot_at_first_zero"]
    assert manifest["mutable_slots"] == 64 and manifest["eligible_blocks"] == 4368
    assert not any(
        manifest[k]
        for k in (
            "hard_pair_floor",
            "fixed_point_degrees",
            "soft_profile_penalty",
            "optimizer_calls",
        )
    )
    assert read(HERE.parent / "pair-two-topmax-proof/audit.json")["passed"]
    assert read(HERE.parent / "native-pair-penalty-independent/postcheck.json")["passed"]
    producer_controls = read(SOURCE / "controls.json")
    assert producer_controls["passed"] and producer_controls["optimizer_calls"] == 0
    assert not producer_controls["positive_zero64_control_available"]
    assert not producer_controls["zero_status_flow_controls_are_candidate_witnesses"]
    assert len(producer_controls["malformed_controls"]) == 7
    assert all(row["returncode"] == 2 for row in producer_controls["malformed_controls"])
    assert not producer_controls["sanitizer_diagnostics"]

    command = [
        "/usr/bin/clang++",
        "-std=c++20",
        "-O1",
        "-g",
        "-fsanitize=address,undefined",
        "-fno-omit-frame-pointer",
        "-Wall",
        "-Wextra",
        "-pedantic",
        str(HERE / "control.cpp"),
        "-o",
        str(RAW / "control"),
    ]
    compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    assert not compiled.stdout and not compiled.stderr
    hints = manifest["hints"]
    assert [row["seed"] for row in hints] == [2026104501, 2026104502]
    assert [row["H"] for row in hints] == [48, 49]
    command = [
        str(RAW / "control"),
        *(str(ROOT / row["path"]) for row in hints),
        str(RAW / "state"),
    ]
    checked = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    (RAW / "control-stdout.json").write_text(checked.stdout)
    (RAW / "control-stderr.txt").write_text(checked.stderr)
    assert not checked.stderr
    controls = json.loads(checked.stdout)
    assert controls["passed"] and controls["optimizer_calls"] == 0
    assert (
        controls["direct_recounts"] == 1306 and controls["shared_pair_contribution_changes"] == 96
    )
    assert controls["commits"] == 522 and controls["rollbacks"] == 530
    assert controls["duplicates"] == 48 and controls["core_rejections"] == 4
    assert controls["accepted_states_below_pair_floor_five"] == 122
    assert controls["intersection_cases"] == [40] * 5
    assert controls["tie_profiles"] == 98304 and controls["extremal_profiles"] == 31521
    assert controls["flow_controls"] == 4488
    (HERE / "control.json").write_text(json.dumps(controls, indent=2, sort_keys=True) + "\n")
    metrics = []
    for row in hints:
        path = ROOT / row["path"]
        assert sha(path) == row["sha256"]
        expected = recount(path, manifest["core_rows"])
        process = subprocess.run(
            [str(ROOT / manifest["binary_path"]), "--metrics", str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert not process.stderr and json.loads(process.stdout) == expected
        assert expected["D2max"] == row["D2max"] and expected["D2sum"] == row["D2sum"]
        assert expected["D3"] == expected["D4"] == 0 and not expected["forbidden"]
        assert expected["core_overlaps"] == row["core_overlaps"]
        metrics.append(expected)
    events = [json.loads(line) for line in (RAW / "state-flow.jsonl").read_text().splitlines()]
    assert [event["role"] for event in events[:3]] == ["raw", "primary", "primary"]
    assert [event["event"] for event in events[3:]] == ["finished", "interrupted"]
    for index, event in enumerate(events[:3]):
        assert event["serial"] == index + 1
        path = RAW / f"state-record-{index + 1}-{event['role']}.txt"
        assert event["metrics"] == recount(path, manifest["core_rows"])
    for event, suffix in zip(events[3:], ("normal", "signal"), strict=True):
        assert event["qualified"] is None
        for role, expected in (
            ("current", metrics[0]),
            ("raw", metrics[0]),
            ("primary", metrics[1]),
        ):
            assert event[role] == expected
            assert (
                recount(RAW / f"state-{suffix}-final-{role}.txt", manifest["core_rows"]) == expected
            )
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": sha(__file__),
        "manifest_sha256": EXPECTED_MANIFEST,
        "source_sha256": manifest["source_sha256"],
        "runner_sha256": manifest["runner_sha256"],
        "binary_sha256": manifest["binary_sha256"],
        "controls": controls,
        "independent_control_source_sha256": sha(HERE / "control.cpp"),
        "independent_expected_tables_sha256": sha(HERE / "expected.hpp"),
        "independent_control_sha256": sha(HERE / "control.json"),
        "sanitizers": ["address", "undefined"],
        "hints": metrics,
        "source_review": "D2 scans14 distinct triple positions, with ties retained. The affected "
        "pair union includes shared pairs with unchanged pair counts. Moves and rollbacks update "
        "all exact counts; four hard caps55 are the only new rejection. Energy is20*D2max+H and "
        "acceptance divides its change by20. Primary records and restarts use lex(D2max,H). "
        "The first zero score stops the native loop and entire pilot, and the runner saves skipped "
        "seeds, actual calls and stop reason without reallocating budget. Every saved state is "
        "recounted and double-verified by the runner; a positive-hole zero score is only a hint.",
        "limitation": "No actual zero-D2 64-family is available as a positive end-to-end stop "
        "control. Exhaustive scalar flow controls and source review check that branch, while "
        "forged zero metrics and false success status are rejected. These are not witnesses.",
        "scope": "GO is limited to seed2026104501/H48 then, only if no qualified hint is found, "
        "seed2026104502/H49; each gets the declared60-second native budget. Timing is logged "
        "separately from the75-second watchdog and5-second termination grace. No extra runs.",
        "raw_files": {
            str(p.relative_to(ROOT)): sha(p) for p in sorted(RAW.iterdir()) if p.is_file()
        },
    }
    (HERE / "gate.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "gate_sha256": sha(HERE / "gate.json"),
                "manifest_sha256": EXPECTED_MANIFEST,
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
