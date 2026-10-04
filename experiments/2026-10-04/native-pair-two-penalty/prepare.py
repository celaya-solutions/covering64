# Document:    Native Compact Pair-Two Preparation and Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e59c5467885fde80210f60e48f6d2bda5561cad785b9b0fee7af4886b8d15c81
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Build and freeze a phase-1 hint search using direct controls only."""

import hashlib
import importlib.util
import itertools
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
RAW = ROOT / "experiments/scratch/native-pair-two-penalty-20261004"
BASE = DAY / "native-pair-penalty"
PLAN = DAY / "native-pair-two-penalty-plan/plan.json"
PROFILE_BAD = DAY / "six-hole-strong-core-release/full-4368/best-04-h8-c1.txt"
CORE_BAD = ROOT / (
    "experiments/2026-10-03/reduced-family-heuristic/penalty-2026100363/"
    "search-control_before-1-h6.txt"
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def call(command, label, timeout=90):
    process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    (RAW / f"{label}-stdout.txt").write_text(process.stdout)
    (RAW / f"{label}-stderr.txt").write_text(process.stderr)
    assert process.returncode == 0 and not process.stderr, (
        label,
        process.returncode,
        process.stderr,
    )
    return process


def main():
    assert not (HERE / "manifest.json").exists() and not (RAW / "start.json").exists()
    RAW.mkdir(parents=True, exist_ok=True)
    plan = json.loads(PLAN.read_text())
    assert plan["phase_count"] == 1 and plan["stop_entire_pilot_on_first_zero"]
    assert plan["budget"]["max_runs"] == 2 and plan["budget"]["stop_after_first_D2max_zero"]
    for relative, digest in plan["input_files"].items():
        assert sha(ROOT / relative) == digest, relative
    proof_path = DAY / "pair-two-topmax-proof/manifest.json"
    proof = json.loads(proof_path.read_text())
    assert proof["passed"]
    for relative, digest in proof["files"].items():
        assert sha(ROOT / relative) == digest
    for new, old in [
        ("native_pair_base.cpp", "search.cpp"),
        ("native_core_base.cpp", "native_core_base.cpp"),
        ("heuristic_search.cpp", "heuristic_search.cpp"),
        ("cores.hpp", "cores.hpp"),
    ]:
        assert sha(HERE / new) == sha(BASE / old)
    fourth = json.loads((DAY / "fourth-core-independent/audit.json").read_text())
    assert fourth["passed"] and fourth["recommended_upper_bound"] == 55
    old_manifest = json.loads((BASE / "manifest.json").read_text())
    cores = old_manifest["core_rows"] + [fourth["core_global_ids"]]
    assert cores == plan["hard_constraints"]["core_rows"]
    expected = "#pragma once\n#include <array>\nconstexpr std::array<int,60> FOURTH_CORE_IDS{{"
    expected += ",".join(map(str, fourth["core_global_ids"])) + "}};\n"
    assert "".join((HERE / "fourth_core.hpp").read_text().splitlines(keepends=True)[9:]) == expected
    compiler = shutil.which("clang++")
    assert compiler
    binary, sanitizer = RAW / "search", RAW / "controls-sanitized"
    build = [
        compiler,
        "-std=c++20",
        "-O3",
        "-DNDEBUG",
        "-Wall",
        "-Wextra",
        "-pedantic",
        str(HERE / "search.cpp"),
        "-o",
        str(binary),
    ]
    sanitize_build = [
        compiler,
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
        str(sanitizer),
    ]
    call(build, "build")
    call(sanitize_build, "sanitizer-build")
    hints = plan["hints"]
    command = [
        str(sanitizer),
        str(ROOT / hints[0]["path"]),
        str(ROOT / hints[1]["path"]),
        str(PROFILE_BAD),
        str(CORE_BAD),
        str(RAW / "control"),
    ]
    direct = json.loads(call(command, "sanitizer-controls").stdout)
    assert direct["passed"] and direct["optimizer_calls"] == 0
    spec = importlib.util.spec_from_file_location("strong_recorder", HERE / "run.py")
    recorder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recorder)
    checked_hints = []
    for hint in hints:
        path = ROOT / hint["path"]
        metrics = json.loads(
            call([str(binary), "--metrics", str(path)], f"hint-{hint['seed']}").stdout
        )
        expected_metrics = {
            "holes": hint["H"],
            "D2max": hint["D2max"],
            "D2sum": hint["D2sum"],
            "D3": 0,
            "D4": 0,
            "energy": hint["proposed_initial_energy"],
            "pair_min": 5,
            "forbidden": False,
            "core_overlaps": hint["core_overlaps"],
        }
        assert metrics == expected_metrics
        checked = recorder.checked(path, cores, True, hint["H"])
        assert checked["metrics"] == expected_metrics
        checked_hints.append(checked)
    events = [json.loads(line) for line in (RAW / "control-events.jsonl").read_text().splitlines()]
    finishes = [row for row in events if row["event"] in ("finished", "interrupted")]
    assert len(finishes) == 2
    assert finishes[0]["current"]["forbidden"] and not finishes[1]["current"]["forbidden"]
    assert all(row["qualified"] is None for row in finishes)
    assert [(r["iterations"], r["restarts"], r["core_rejections"]) for r in finishes] == [
        (123, 4, 5),
        (456, 7, 8),
    ]
    checked_controls = [
        recorder.checked(path, cores, "raw" in path.name)
        for path in sorted(RAW.glob("control*.txt"))
    ]
    assert checked_controls
    watchdogs = []
    for label in ["ordinary", "terminate", "kill"]:
        child = RAW / f"watchdog-{label}.py"
        if label == "ordinary":
            code = "print('ordinary')\n"
        elif label == "terminate":
            code = (
                "import signal,time,sys\n"
                "signal.signal(signal.SIGTERM,lambda *args:sys.exit(0))\n"
                "print('ready',flush=True)\ntime.sleep(10)\n"
            )
        else:
            code = (
                "import signal,time\nsignal.signal(signal.SIGTERM,signal.SIG_IGN)\n"
                "print('ready',flush=True)\ntime.sleep(10)\n"
            )
        fields = [
            ("Document", f"Strong Pair Watchdog {label} Control"),
            ("Version", "v1.0.0"),
            ("Author", "Celaya Solutions"),
            ("Contact", "hello@celayasolutions.com"),
            ("Date", "2026-10-04"),
            ("SHA256", hashlib.sha256(code.encode()).hexdigest()),
            ("Chain", "n/a"),
            ("Tx", "[not anchored]"),
            ("License", "All Rights Reserved / Celaya Solutions"),
        ]
        child.write_text("".join(f"# {key + ':':<13}{value}\n" for key, value in fields) + code)
        rc, stdout, stderr, watchdog, elapsed = recorder.execute_bounded(
            [sys.executable, str(child)], deadline=0.5, grace=0.25
        )
        assert not stderr and not watchdog["relaunch"]
        assert watchdog["fired"] == watchdog["terminate_sent"] == (label != "ordinary")
        assert watchdog["kill_sent"] == (label == "kill") and rc == (-9 if label == "kill" else 0)
        watchdogs.append(
            {
                "label": label,
                "returncode": rc,
                "stdout": stdout,
                "watchdog": watchdog,
                "elapsed_seconds": elapsed,
                "sha256": sha(child),
            }
        )
    malformed = []
    original = (ROOT / hints[0]["path"]).read_text().splitlines()
    for label in [
        "duplicate",
        "label_zero",
        "label_high",
        "token",
        "block_size",
        "count63",
        "count65",
    ]:
        lines = original.copy()
        if label == "duplicate":
            lines[-1] = lines[0]
        elif label == "label_zero":
            lines[0] = "0 2 3 4 5"
        elif label == "label_high":
            lines[0] = "1 2 3 4 17"
        elif label == "token":
            lines[0] = "1 2 3 4 nope"
        elif label == "block_size":
            lines[0] = "1 2 3 4"
        elif label == "count63":
            lines.pop()
        else:
            present = {tuple(map(int, line.split())) for line in lines}
            lines.append(
                " ".join(
                    map(
                        str,
                        next(
                            b for b in itertools.combinations(range(1, 17), 5) if b not in present
                        ),
                    )
                )
            )
        path = RAW / f"damaged-{label}.txt"
        path.write_text("\n".join(lines) + "\n")
        process = subprocess.run(
            [str(binary), "--metrics", str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert process.returncode == 2 and process.stderr
        malformed.append(
            {
                "label": label,
                "returncode": process.returncode,
                "stderr": process.stderr,
                "sha256": sha(path),
            }
        )
    dump(
        HERE / "controls.json",
        {
            "passed": True,
            "optimizer_calls": 0,
            "sanitizer_command": command,
            "sanitizer_diagnostics": "",
            "direct_controls": direct,
            "hints": checked_hints,
            "finish_events": finishes,
            "checked_snapshots": checked_controls,
            "watchdog_controls": watchdogs,
            "malformed_controls": malformed,
            "positive_zero64_control_available": False,
            "zero_status_flow_controls_are_candidate_witnesses": False,
        },
    )
    inputs = dict(plan["input_files"])
    paths = [PLAN, PROFILE_BAD, CORE_BAD, HERE / "controls.json"]
    paths += sorted(HERE.glob("*.cpp")) + sorted(HERE.glob("*.hpp")) + sorted(HERE.glob("*.py"))
    for path in paths:
        inputs[str(path.relative_to(ROOT))] = sha(path)
    manifest = {
        "prepared_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "input_files": inputs,
        "raw_files": {
            str(path.relative_to(ROOT)): sha(path)
            for path in sorted(RAW.iterdir())
            if path.is_file()
        },
        "source_sha256": sha(HERE / "search.cpp"),
        "runner_sha256": sha(HERE / "run.py"),
        "binary_path": str(binary.relative_to(ROOT)),
        "binary_sha256": sha(binary),
        "sanitizer_binary_sha256": sha(sanitizer),
        "compiler_path": compiler,
        "compiler_sha256": sha(compiler),
        "compiler_version": subprocess.check_output([compiler, "--version"], text=True),
        "build_command": build,
        "sanitizer_build_command": sanitize_build,
        "core_rows": cores,
        "core_upper_bound": 55,
        "controls_sha256": sha(HERE / "controls.json"),
        "hints": hints,
        "budget": plan["budget"],
        "plan_sha256": sha(PLAN),
        "energy": "20*D2max+H",
        "metropolis_delta": "integer energy change divided by20",
        "best_restart_key": ["D2max", "H"],
        "tie_policy": "first encountered",
        "restart_steps": 1500000,
        "restart_source": "original every third, otherwise primary lex best",
        "temperature": "0.06+(0.7+0.1*(restarts%4))*(1-step/1500000)^3",
        "audit_period": 4096,
        "phase_count": 1,
        "stop_entire_pilot_at_first_zero": True,
        "mutable_slots": 64,
        "eligible_blocks": 4368,
        "hard_pair_floor": False,
        "fixed_point_degrees": False,
        "soft_profile_penalty": False,
        "optimizer_calls": 0,
        "scope": (
            "Phase 1 only: seek a strong-cut partial hint, stop at first actual D2max=0. "
            "No cover or lower-bound claim from positive holes or bounded failure."
        ),
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "source_sha256": manifest["source_sha256"],
                "runner_sha256": manifest["runner_sha256"],
                "binary_sha256": sha(binary),
                "controls_sha256": sha(HERE / "controls.json"),
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
