# Document:    Native Core-Cap Escape Preparation and Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      3f45ba7f777af193f8d8ff4bd71dd64408f9e0ad964b493875e6582000b17835
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Build and exercise deterministic controls; never enter the search main loop."""

import copy
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
RAW = ROOT / "experiments/scratch/native-core-cap-escape-20261004"
HINT = DAY / "six-hole-strong-core-release/full-4368/best-03-h10-c1.txt"
PROFILE_BAD = DAY / "six-hole-strong-core-release/full-4368/best-04-h8-c1.txt"
CORE_BAD = DAY / "six-hole-strong-core-release/full-4368/final-response.txt"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
TRIPLES = list(itertools.combinations(range(1, 17), 3))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def header(title, body, comment="//"):
    fields = [
        ("Document", title),
        ("Version", "v1.0.0"),
        ("Author", "Celaya Solutions"),
        ("Contact", "hello@celayasolutions.com"),
        ("Date", "2026-10-04"),
        ("SHA256", hashlib.sha256(body.encode()).hexdigest()),
        ("Chain", "n/a"),
        ("Tx", "[not anchored]"),
        ("License", "All Rights Reserved / Celaya Solutions"),
    ]
    return "".join(f"{comment} {name + ':':<13}{value}\n" for name, value in fields) + body


def validate_rows(rows, expected):
    assert len(rows) == 3
    assert all(len(row) == len(set(row)) == 60 for row in rows)
    assert all(all(isinstance(i, int) and 0 <= i < 4368 for i in row) for row in rows)
    assert rows == expected


def validate_dump(actual, rows):
    assert actual["cap"] == 55
    assert actual["block_masks"] == [sum(1 << (x - 1) for x in b) for b in BLOCKS]
    assert actual["triple_masks"] == [sum(1 << (x - 1) for x in t) for t in TRIPLES]
    assert actual["membership"] == [
        sum((1 << c) for c, row in enumerate(rows) if i in row) for i in range(4368)
    ]


def rejected(operation):
    try:
        operation()
    except (AssertionError, ValueError, KeyError):
        return True
    raise AssertionError("Damaged control was accepted")


def call(command, label, timeout=60):
    process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    (RAW / f"{label}-stdout.txt").write_text(process.stdout)
    (RAW / f"{label}-stderr.txt").write_text(process.stderr)
    assert process.returncode == 0, (label, process.returncode, process.stderr)
    return process


def main():
    assert not (HERE / "manifest.json").exists()
    assert not (RAW / "start.json").exists()
    RAW.mkdir(parents=True, exist_ok=True)
    plan_path = DAY / "native-core-cap-escape-plan/plan.json"
    plan = json.loads(plan_path.read_text())
    for relative, digest in plan["input_files"].items():
        assert sha(ROOT / relative) == digest
    basis_path = DAY / "three-core-profile-release/manifest.json"
    basis = json.loads(basis_path.read_text())
    cap_path = DAY / "core-cap-independent/audit.json"
    third_path = DAY / "third-core-independent/audit.json"
    cap, third = json.loads(cap_path.read_text()), json.loads(third_path.read_text())
    assert cap["passed"] and third["passed"]
    assert cap["recommended_upper_bound"] == third["recommended_upper_bound"] == 55
    expected = [row["core_global_ids"] for row in cap["current_core_translations"]]
    expected += [third["core_global_ids"]]
    rows = basis["core_rows"]
    validate_rows(rows, expected)
    assert sha(HERE / "heuristic_search.cpp") == sha(ROOT / "scripts/heuristic_search.cpp")
    body = "\n#pragma once\n#include <array>\nconstexpr int CORE_CAP = 55;\n"
    body += "constexpr std::array<std::array<int, 60>, 3> CORE_IDS{{\n"
    body += "".join("  {{" + ", ".join(map(str, row)) + "}},\n" for row in rows)
    body += "}};\n"
    (HERE / "cores.hpp").write_text(header("Three Audited Core Membership Rows", body))
    compiler = shutil.which("clang++")
    assert compiler
    version = subprocess.check_output([compiler, "--version"], text=True)
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
    table = json.loads(call([str(binary), "--dump-cores"], "table").stdout)
    validate_dump(table, rows)
    damaged_tables = []
    for label, field in [
        ("cap54", "cap"),
        ("wrong_block_order", "block_masks"),
        ("wrong_triple_order", "triple_masks"),
        ("wrong_membership", "membership"),
    ]:
        altered = copy.deepcopy(table)
        if field == "cap":
            altered[field] = 54
        elif field == "membership":
            altered[field][rows[2][0]] ^= 4
        else:
            altered[field][0], altered[field][1] = altered[field][1], altered[field][0]
        assert rejected(lambda: validate_dump(altered, rows))
        damaged_tables.append(label)
    for label in ["duplicate_id", "missing_id", "wrong_id", "wrong_transport"]:
        altered = copy.deepcopy(rows)
        if label == "duplicate_id":
            altered[2][1] = altered[2][0]
        elif label == "missing_id":
            altered[2].pop()
        elif label == "wrong_id":
            altered[2][0] = next(i for i in range(4368) if i not in altered[2])
        else:
            altered[2] = altered[0]
        assert rejected(lambda: validate_rows(altered, expected))
        damaged_tables.append(label)
    harness_command = [
        str(sanitizer),
        str(HINT),
        str(PROFILE_BAD),
        str(CORE_BAD),
        str(RAW / "control-record.txt"),
    ]
    harness = call(harness_command, "sanitizer-controls", timeout=120)
    assert not harness.stderr
    controls = json.loads(harness.stdout)
    assert controls["boundaries"] == 9 and controls["membership_transitions"] == 24
    profiles = {}
    for label, path in [("hint", HINT), ("profile_bad", PROFILE_BAD), ("core_bad", CORE_BAD)]:
        profiles[label] = json.loads(call([str(binary), "--profile", str(path)], label).stdout)
    assert profiles["hint"] == {
        "missing": 10,
        "forbidden": False,
        "core_overlaps": [1, 8, 55],
        "caps_pass": True,
    }
    assert profiles["profile_bad"]["forbidden"] and profiles["profile_bad"]["caps_pass"]
    assert profiles["core_bad"]["core_overlaps"][2] == 60
    assert not profiles["core_bad"]["caps_pass"]
    spec = importlib.util.spec_from_file_location("native_core_recorder", HERE / "run.py")
    recorder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recorder)
    watchdog_controls = []
    child = RAW / "watchdog-control.py"
    for label in ["ordinary", "terminate", "kill"]:
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
        child.write_text(code)
        returncode, stdout, stderr, watchdog, elapsed = recorder.execute_bounded(
            [sys.executable, str(child)],
            deadline=0.5,
            grace=0.25,
        )
        assert not stderr and not watchdog["relaunch"]
        assert watchdog["fired"] == (label != "ordinary")
        assert watchdog["terminate_sent"] == (label != "ordinary")
        assert watchdog["kill_sent"] == (label == "kill")
        assert returncode == (-9 if label == "kill" else 0)
        watchdog_controls.append(
            {
                "label": label,
                "returncode": returncode,
                "stdout": stdout,
                "watchdog": watchdog,
                "elapsed_seconds": elapsed,
                "control_sha256": sha(child),
            }
        )
    from covering64.core import read_blocks, verify_cover

    witness = read_blocks(HINT)
    package = verify_cover(witness)
    standalone = subprocess.run(
        [sys.executable, "scripts/check_cover.py", str(HINT), "--expected-blocks", "64"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert standalone.returncode == 1
    standalone_data = json.loads(standalone.stdout)
    assert len(witness) == len(set(witness)) == 64
    assert len(package["uncovered"]) == standalone_data["uncovered_count"] == 10
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
            lines.append(" ".join(map(str, next(b for b in BLOCKS if b not in present))))
        path = RAW / f"damaged-{label}.txt"
        path.write_text("\n".join(lines) + "\n")
        process = subprocess.run(
            [str(binary), "--profile", str(path)],
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
    result = {
        "passed": True,
        "optimizer_calls": 0,
        "control_execution_kind": "direct predicates and transitions",
        "native_membership_entries": 13104,
        "native_blocks": 4368,
        "native_triples": 560,
        "damaged_table_controls_rejected": damaged_tables,
        "transition_controls": controls,
        "profiles": profiles,
        "malformed_controls": malformed,
        "watchdog_controls": watchdog_controls,
        "hint_verifiers": {"package": package, "standalone": standalone_data},
        "sanitizer_diagnostics": harness.stderr,
        "sanitizer_command": harness_command,
    }
    dump(HERE / "controls.json", result)
    inputs = dict(plan["input_files"])
    for path in [
        plan_path,
        PROFILE_BAD,
        CORE_BAD,
        HERE / "search.cpp",
        HERE / "heuristic_search.cpp",
        HERE / "cores.hpp",
        HERE / "control.cpp",
        HERE / "prepare.py",
        HERE / "run.py",
        HERE / "controls.json",
    ]:
        inputs[str(path.relative_to(ROOT))] = sha(path)
    raw_files = {
        str(path.relative_to(ROOT)): sha(path) for path in sorted(RAW.iterdir()) if path.is_file()
    }
    manifest = {
        "prepared_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "input_files": inputs,
        "raw_files": raw_files,
        "source_sha256": sha(HERE / "search.cpp"),
        "runner_sha256": sha(HERE / "run.py"),
        "binary_path": str(binary.relative_to(ROOT)),
        "binary_sha256": sha(binary),
        "sanitizer_binary_sha256": sha(sanitizer),
        "compiler_path": compiler,
        "compiler_version": version,
        "compiler_sha256": sha(compiler),
        "build_command": build,
        "sanitizer_build_command": sanitize_build,
        "core_rows": rows,
        "core_upper_bound": 55,
        "controls_sha256": sha(HERE / "controls.json"),
        "hint_path": str(HINT.relative_to(ROOT)),
        "hint_sha256": sha(HINT),
        "hint_holes": 10,
        "hint_core_overlaps": [1, 8, 55],
        "budget": {
            "runs": 2,
            "seconds_per_run": 60,
            "seeds": [2026104201, 2026104202],
            "watchdog_seconds": 75,
            "termination_grace_seconds": 5,
            "simultaneous_processes": 1,
            "relaunch": False,
        },
        "optimizer_calls": 0,
        "scope": (
            "Full 64-slot native construction with three hard core caps and unchanged "
            "soft global-profile traversal/eligible recording. "
            "No connectivity or nonexistence claim."
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
