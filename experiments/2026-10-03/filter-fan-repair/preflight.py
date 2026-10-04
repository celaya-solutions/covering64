# Document:    Filter-and-Fan Prototype Preflight and Frozen Evidence
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      a692b6f60e327ee4bb37465a31c7c5b535e72a82d02f55f943d43b44223dccf9
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Compile and check the prototype; no paired research pilots are launched."""

import argparse
import hashlib
import json
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from covering64.core import read_blocks, verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SEED = ROOT / "experiments/scratch/heuristic-tabu-2026100301-deficit-3.txt"


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    require(not output.exists(), "new immutable directory required")
    output.mkdir(parents=True)
    commands = []

    def run(command, label, expected=0):
        began = time.monotonic()
        result = subprocess.run([str(x) for x in command], cwd=ROOT, text=True,
                                capture_output=True, timeout=45, check=False)
        (output / f"{label}.stdout").write_text(result.stdout)
        (output / f"{label}.stderr").write_text(result.stderr)
        commands.append(dict(command=[str(x) for x in command], label=label,
                             returncode=result.returncode, elapsed=time.monotonic() - began))
        require(result.returncode == expected, f"unexpected return code: {label}")
        return result

    for path in (HERE / "search.cpp", HERE / "check_traces.py", Path(__file__), SEED,
                 ROOT / "scripts/check_cover.py", ROOT / "src/covering64/core.py"):
        (output / path.name).write_bytes(path.read_bytes())
    package = verify_cover(read_blocks(SEED))
    require(package["canonical_sha256"] ==
            "d6dcfd2f1778f76c90ca67698865f683a44a6b69ddacad8f77cc4ee9021eacdf"
            and package["blocks"] == 64 and len(package["uncovered"]) == 3, "frozen seed")
    standalone = json.loads(run([sys.executable, ROOT / "scripts/check_cover.py", SEED,
                                 "--v", 16, "--k", 5, "--t", 3], "seed-check", 1).stdout)
    require(standalone["uncovered_count"] == 3 and not standalone["valid"], "seed check")
    (output / "seed-package.json").write_text(json.dumps(package, indent=2) + "\n")
    compiler = run(["clang++", "--version"], "compiler").stdout
    common = ["clang++", "-std=c++17", "-Wall", "-Wextra", "-Wpedantic", "-Werror"]
    binary, sanitizer = output / "search", output / "search-san"
    for name, executable, flags in (
        ("release", binary, ["-O2"]),
        ("sanitizer", sanitizer, ["-O1", "-g", "-fsanitize=address,undefined",
                                  "-fno-omit-frame-pointer"]),
    ):
        run([*common, *flags, HERE / "search.cpp", "-o", executable], f"compile-{name}")
        result = run([executable, "--self-test", SEED, output / name], f"controls-{name}")
        require(not result.stderr and json.loads(result.stdout)["passed"], "native controls")
    seed_lines = SEED.read_text().splitlines()
    mutations = {
        "63-blocks": seed_lines[:-1], "65-blocks": seed_lines + ["1 2 3 4 5"],
        "duplicate-block": [seed_lines[1], *seed_lines[1:]],
        "duplicate-point": ["1 1 3 4 6", *seed_lines[1:]],
        "zero-point": ["0 2 3 4 6", *seed_lines[1:]],
        "large-point": ["1 2 3 4 17", *seed_lines[1:]],
        "short-block": ["1 2 3 4", *seed_lines[1:]],
        "bad-token": ["1x 2 3 4 6", *seed_lines[1:]], "empty": [],
    }
    invalid = []
    for label, lines in mutations.items():
        path = output / f"invalid-{label}.txt"
        path.write_text("\n".join(lines) + "\n")
        run([binary, path, 2026100360, .001, "beam", output / "invalid"], label, 2)
        invalid.append(label)
    for label, parameters in (
        ("zero-time", [2026100360, 0, "beam"]),
        ("negative-time", [2026100360, -1, "beam"]),
        ("nan-time", [2026100360, "nan", "beam"]),
        ("junk-time", [2026100360, "1junk", "beam"]),
        ("negative-seed", [-1, .001, "beam"]),
        ("bad-mode", [2026100360, .001, "unknown"]),
    ):
        run([binary, SEED, *parameters, output / "invalid"], label, 2)
        invalid.append(label)
    run([binary, SEED, 2026100360, .001, "beam", output / "invalid", 0, 6, 12],
        "bad-width", 2)
    invalid.append("bad-width")
    run([binary, SEED, 2026100360, .001, "beam", output / "missing/output"],
        "unwritable-output", 2)
    invalid.append("unwritable-output")
    smoke = []
    for mode in ("beam", "greedy"):
        prefix = output / mode
        result = run([sanitizer, SEED, 2026100360, .25, mode, prefix], mode)
        require(not result.stderr, "sanitizer diagnostics")
        final = json.loads(result.stdout.splitlines()[-1])
        require(final["event"] == "final" and final["elapsed"] < 1.25, "bounded smoke")
        report = verify_cover(read_blocks(output / f"{mode}-best.txt"))
        check = json.loads(run([sys.executable, ROOT / "scripts/check_cover.py",
                               output / f"{mode}-best.txt", "--v", 16, "--k", 5, "--t", 3],
                              f"{mode}-check", 0 if report["valid"] else 1).stdout)
        require(check["uncovered_count"] == len(report["uncovered"]) == final["best_deficit"]
                and check["blocks"] == report["blocks"] == 64, "smoke candidate check")
        (output / f"{mode}-package.json").write_text(json.dumps(report, indent=2) + "\n")
        smoke.append(dict(mode=mode, **final))
    process = subprocess.Popen([str(binary), str(SEED), "2026100360", "10", "beam",
                                str(output / "interrupted")], cwd=ROOT, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    first = process.stdout.readline()
    require(json.loads(first)["mode"] == "beam", "interrupt readiness")
    time.sleep(.05)
    process.send_signal(signal.SIGTERM)
    stdout, stderr = process.communicate(timeout=5)
    (output / "interrupted.stdout").write_text(first + stdout)
    (output / "interrupted.stderr").write_text(stderr)
    require(process.returncode == 0 and not stderr and
            json.loads(stdout.splitlines()[-1])["interrupted"], "graceful interrupt")
    traces = [output / f"{name}-traces.jsonl" for name in
              ("release", "sanitizer", "beam", "greedy", "interrupted")]
    replay = run([sys.executable, HERE / "check_traces.py", *traces, "--output",
                  output / "replay.json"], "replay")
    require(json.loads(replay.stdout)["passed"], "independent replay")
    result = dict(version="v1.0.0", passed=True, recorded_utc=datetime.now(UTC).isoformat(),
                  source_revision=subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                          cwd=ROOT, text=True).strip(),
                  compiler=compiler, commands=commands, invalid_inputs_rejected=invalid,
                  smoke=smoke, interrupted=True, independent_replay=json.loads(replay.stdout),
                  hashes={str(p.relative_to(ROOT)): sha(p) for p in
                          (HERE / "search.cpp", HERE / "check_traces.py", Path(__file__), SEED,
                           binary, sanitizer, output / "replay.json")},
                  scope="Preflight and 0.25-second smoke only. Paired pilots require root review.")
    (output / "preflight.json").write_text(json.dumps(result, indent=2) + "\n")
    (HERE / "preflight.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(passed=True, output=str(output), smoke=smoke,
                         invalid_inputs_rejected=len(invalid))))


if __name__ == "__main__":
    main()
