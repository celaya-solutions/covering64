# Document:    Heavy Profile Search Campaign Recorder
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      b5b98f45982e98252c4cd0b9e642bcd8c892bfb9416ff7453e3c1b657a65c53e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Save and independently check every strict improvement from one native run."""

import argparse
import hashlib
import itertools
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

from covering64.core import read_blocks, verify_cover


def checked(path, expected_missing=None, eligible=False):
    blocks = read_blocks(path)
    package = verify_cover(blocks)
    process = subprocess.run(
        [sys.executable, "scripts/check_cover.py", str(path), "--expected-blocks", "64"],
        text=True, capture_output=True,
    )
    if process.returncode not in (0, 1):
        raise RuntimeError(process.stderr)
    standalone = json.loads(process.stdout)
    counts = Counter(t for b in blocks for t in itertools.combinations(b, 3))
    missing = 560 - len(counts)
    heavy = [t for t, n in counts.items() if n >= 6]
    forbidden = any(
        len(set().union(*map(set, choice))) == 15
        and sum(counts[t] >= 7 for t in choice) >= 2
        for choice in itertools.combinations(heavy, 5)
    )
    if (len(blocks) != 64 or len(set(blocks)) != 64
            or len(package["uncovered"]) != missing
            or standalone["uncovered_count"] != missing
            or (expected_missing is not None and expected_missing != missing)
            or (eligible and forbidden)):
        raise RuntimeError("Independent candidate recount failed")
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "missing": missing, "forbidden": forbidden, "package": package,
            "standalone": standalone}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("start", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seconds", type=float, default=600)
    parser.add_argument("--seed", type=int, default=2026102401)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    archive = Path("experiments/scratch") / args.output.name
    archive.mkdir(parents=True, exist_ok=False)
    sources = {}
    for name in ("heavy_profile_heuristic.cpp", "heuristic_search.cpp"):
        source = Path("scripts") / name
        shutil.copyfile(source, archive / name)
        sources[name] = hashlib.sha256(source.read_bytes()).hexdigest()
    recorder = Path(__file__)
    shutil.copyfile(recorder, archive / "run.py")
    command = [str(args.binary), str(args.start), str(args.seed), str(args.seconds),
               str(args.output / "search")]
    metadata = {"command": command, "source_sha256": sources,
                "recorder_sha256": hashlib.sha256(recorder.read_bytes()).hexdigest(),
                "source_revision": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True).strip(),
                "binary_sha256": hashlib.sha256(args.binary.read_bytes()).hexdigest(),
                "source_archive": str(archive), "initial": checked(args.start),
                "compiler": subprocess.check_output(["clang++", "--version"], text=True),
                "scope": "Construction heuristic; all blocks free; no nonexistence claim."}
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    records = []
    with (args.output / "stdout.jsonl").open("w") as output, (
            args.output / "stderr.txt").open("w") as errors:
        process = subprocess.Popen(command, text=True, stdout=subprocess.PIPE, stderr=errors)
        try:
            for line in process.stdout:
                output.write(line)
                output.flush()
                event = json.loads(line)
                if event["event"] == "improvement":
                    path = args.output / f"search-h{event['missing']}.txt"
                    records.append(checked(path, event["missing"], True))
                    (args.output / "checks.json").write_text(json.dumps(records, indent=2) + "\n")
                print(line, end="", flush=True)
            code = process.wait()
            if code not in (0, 1):
                raise RuntimeError(f"Search failed with code{code}")
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
    result = {"exit_code": code, "checked_candidates": len(records),
              "best_missing": min((r["missing"] for r in records), default=None),
              "cover_found": any(r["standalone"]["valid"] for r in records)}
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
