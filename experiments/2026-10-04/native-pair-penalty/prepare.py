# Document:    Native Pair Penalty Preparation and Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e574be4f123642f0202c8b0e5a413f810a0766c36d27e406fbcda10c6e42c346
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Freeze deterministic pair arithmetic controls; do not enter optimizer main."""

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
RAW = ROOT / "experiments/scratch/native-pair-penalty-20261004"
HINT = (
    ROOT
    / "experiments/2026-10-03/reduced-family-heuristic/penalty-2026100363"
    / "search-control_before-1-h6.txt"
)
PROFILE_BAD = DAY / "six-hole-strong-core-release/full-4368/best-04-h8-c1.txt"
BASE = DAY / "native-core-cap-escape-v2"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def call(command, label, timeout=90):
    process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    (RAW / f"{label}-stdout.txt").write_text(process.stdout)
    (RAW / f"{label}-stderr.txt").write_text(process.stderr)
    assert process.returncode == 0, (label, process.returncode, process.stderr)
    assert not process.stderr, (label, process.stderr)
    return process


def main():
    assert not (HERE / "manifest.json").exists() and not (RAW / "start.json").exists()
    RAW.mkdir(parents=True, exist_ok=True)
    prior = json.loads((BASE / "manifest.json").read_text())
    for target, original in [
        ("native_core_base.cpp", "search.cpp"),
        ("heuristic_search.cpp", "heuristic_search.cpp"),
        ("cores.hpp", "cores.hpp"),
    ]:
        assert sha(HERE / target) == sha(BASE / original)
    assert sha(HINT) == "797dada195b23eecc808798eb12c8e4e7ccd7edd026fbdf22dea5b341f9ea2de"
    proof_path = DAY / "pair-local-necessary-cuts-independent/audit.json"
    assert sha(proof_path) == "506205cd1e0f8334f0d690c6f4f9929cc08267422285b31935a76a424003e4a8"
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
    controls_command = [str(sanitizer), str(HINT), str(PROFILE_BAD), str(RAW / "control")]
    controls = json.loads(call(controls_command, "sanitizer-controls").stdout)
    assert controls["passed"]
    hint_metrics = json.loads(call([str(binary), "--metrics", str(HINT)], "hint-metrics").stdout)
    assert hint_metrics == {
        "holes": 6,
        "D3": 4,
        "D4": 0,
        "energy": 140,
        "pair_min": 5,
        "forbidden": False,
        "core_overlaps": [2, 2, 0],
    }
    spec = importlib.util.spec_from_file_location("pair_recorder", HERE / "run.py")
    recorder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recorder)
    checked_hint = recorder.checked(HINT, prior["core_rows"], True, 6)
    assert checked_hint["metrics"] == hint_metrics
    events = [json.loads(line) for line in (RAW / "control-events.jsonl").read_text().splitlines()]
    finishes = [event for event in events if event["event"] in ("finished", "interrupted")]
    assert len(finishes) == 2
    assert finishes[0]["current"]["forbidden"] and not finishes[1]["current"]["forbidden"]
    assert all(event["qualified"] is None for event in finishes)
    assert [(e["iterations"], e["restarts"], e["core_rejections"]) for e in finishes] == [
        (123, 4, 5),
        (456, 7, 8),
    ]
    checked_controls = [
        recorder.checked(path, prior["core_rows"], "current" not in path.name)
        for path in sorted(RAW.glob("control*.txt"))
    ]
    assert checked_controls
    watchdog_controls = []
    for label in ["ordinary", "terminate", "kill"]:
        child = RAW / f"watchdog-{label}.py"
        if label == "ordinary":
            code = "print('ordinary')\n"
        elif label == "terminate":
            code = (
                "import signal,time,sys\n"
                "signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))\n"
                "print('ready',flush=True)\ntime.sleep(10)\n"
            )
        else:
            code = (
                "import signal,time\nsignal.signal(signal.SIGTERM,signal.SIG_IGN)\n"
                "print('ready',flush=True)\ntime.sleep(10)\n"
            )
        fields = [
            ("Document", f"Watchdog {label} Control"),
            ("Version", "v1.0.0"),
            ("Author", "Celaya Solutions"),
            ("Contact", "hello@celayasolutions.com"),
            ("Date", "2026-10-04"),
            ("SHA256", hashlib.sha256(code.encode()).hexdigest()),
            ("Chain", "n/a"),
            ("Tx", "[not anchored]"),
            ("License", "All Rights Reserved / Celaya Solutions"),
        ]
        child.write_text("".join(f"# {key + chr(58):<13}{value}\n" for key, value in fields) + code)
        rc, stdout, stderr, watchdog, elapsed = recorder.execute_bounded(
            [sys.executable, str(child)], deadline=0.5, grace=0.25
        )
        assert not stderr and not watchdog["relaunch"]
        assert watchdog["fired"] == watchdog["terminate_sent"] == (label != "ordinary")
        assert watchdog["kill_sent"] == (label == "kill")
        assert rc == (-9 if label == "kill" else 0)
        watchdog_controls.append(
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
    original = HINT.read_text().splitlines()
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
        p = subprocess.run(
            [str(binary), "--metrics", str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert p.returncode == 2 and p.stderr
        malformed.append(
            {"label": label, "returncode": p.returncode, "stderr": p.stderr, "sha256": sha(path)}
        )
    dump(
        HERE / "controls.json",
        {
            "passed": True,
            "optimizer_calls": 0,
            "sanitizer_diagnostics": "",
            "sanitizer_command": controls_command,
            "transition_controls": controls,
            "hint": checked_hint,
            "finish_events": finishes,
            "checked_snapshots": checked_controls,
            "malformed_controls": malformed,
            "watchdog_controls": watchdog_controls,
        },
    )
    paths = [
        HINT,
        PROFILE_BAD,
        proof_path,
        BASE / "manifest.json",
        BASE / "controls.json",
        DAY / "native-core-cap-escape-independent/gate.json",
    ]
    paths += sorted(HERE.glob("*.cpp")) + sorted(HERE.glob("*.hpp")) + sorted(HERE.glob("*.py"))
    paths += [HERE / "controls.json"]
    manifest = {
        "prepared_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "input_files": {str(path.relative_to(ROOT)): sha(path) for path in paths},
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
        "core_rows": prior["core_rows"],
        "core_upper_bound": 55,
        "controls_sha256": sha(HERE / "controls.json"),
        "hint_path": str(HINT.relative_to(ROOT)),
        "hint_sha256": sha(HINT),
        "hint_metrics": hint_metrics,
        "energy": "20H + 5D3 + D4 + 160F",
        "row_counts": {"D3": 1680, "D4": 10920},
        "restart": (
            "every third original hint, otherwise best profile-clear "
            "(integer energy,D3+D4,holes), first tie retained"
        ),
        "restart_steps": 1500000,
        "audit_period": 4096,
        "temperature": "0.06+(0.7+0.1*(restarts%4))*(1-step/1500000)^3",
        "metropolis_delta": "integer energy change divided by20; one uniform consumed per proposal",
        "mutable_slots": 64,
        "eligible_blocks": 4368,
        "hard_pair_floor": False,
        "fixed_point_degrees": False,
        "budget": {
            "runs": 2,
            "seconds_per_run": 60,
            "seeds": [2026104401, 2026104402],
            "watchdog_seconds": 75,
            "termination_grace_seconds": 5,
            "simultaneous_processes": 1,
            "relaunch": False,
        },
        "optimizer_calls": 0,
        "scope": (
            "Construction heuristic with three named hard core caps and soft global "
            "profile/pair penalties. No completeness or lower bound claim."
        ),
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "source_sha256": manifest["source_sha256"],
                "binary_sha256": sha(binary),
                "controls_sha256": sha(HERE / "controls.json"),
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
