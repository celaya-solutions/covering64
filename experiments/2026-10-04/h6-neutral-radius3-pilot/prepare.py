# Document:    H6 Neutral Radius-Three Diagnostic Preparation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      aafb15f715ffba804eddede00f8f4867d779b4ca6ca445206342da4786b1b532
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Compile, check tiny fixtures without pruning, reject corruptions, and freeze."""

import csv
import hashlib
import importlib.util
import itertools
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/h6-neutral-radius3-pilot-20261004"
INPUT = HERE.parent / "native-h9-h10-reuse-pilot/seed-2026105901/search-final-raw64.txt"
INPUT_SHA = "2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def invoke(binary, source, holes, target, name, seconds, count, fixture=False):
    output = RAW / name
    output.mkdir()
    command = [
        str(binary),
        str(source),
        str(holes),
        str(target),
        str(output),
        str(seconds),
        str(count),
    ]
    if fixture:
        command += ["--fixture-v", "7"]
    process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=15)
    (RAW / f"{name}-stdout.txt").write_text(process.stdout)
    (RAW / f"{name}-stderr.txt").write_text(process.stderr)
    return output, process


def fixture_check(binary, fixture_ids, index):
    blocks = list(itertools.combinations(range(1, 8), 5))
    triples = set(itertools.combinations(range(1, 8), 3))
    covered = [set(itertools.combinations(block, 3)) for block in blocks]
    original = set(fixture_ids)
    holes = len(triples - set().union(*(covered[i] for i in original)))
    assert holes > 0
    source = RAW / f"fixture-{index}.txt"
    source.write_text("".join(" ".join(map(str, blocks[i])) + "\n" for i in sorted(original)))
    output, process = invoke(
        binary, source, holes, holes, f"fixture-{index}-output", 10, len(original), True
    )
    assert process.returncode == 0 and not process.stderr
    summary = json.loads(process.stdout)
    assert summary["status"] == "complete"
    expected, tuples = {}, 0
    # Independent oracle: every deletion and every unselected addition tuple,
    # direct sets of labeled triples, no carrier counts, bounds, floors, or masks.
    for distance in (1, 2, 3):
        for deleted in itertools.combinations(sorted(original), distance):
            kept = original - set(deleted)
            for added in itertools.combinations(
                sorted(set(range(len(blocks))) - original), distance
            ):
                tuples += 1
                family = kept | set(added)
                missing = len(triples - set().union(*(covered[i] for i in family)))
                if missing <= holes:
                    expected[tuple(sorted(family))] = (distance, missing, deleted, added)
    actual = {}
    rows = list(csv.DictReader((output / "candidates.tsv").open(), delimiter="\t"))
    assert [int(row["candidate"]) for row in rows] == list(range(1, len(rows) + 1))
    rank = {block: i for i, block in enumerate(blocks)}
    for row in rows:
        path = output / f"candidate-{row['candidate']}.txt"
        parsed = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
        family = tuple(rank[block] for block in parsed)
        assert len(family) == len(set(family)) == len(original)
        assert family == tuple(sorted(family)) and family not in actual
        actual[family] = (
            int(row["distance"]),
            int(row["holes"]),
            tuple(map(int, row["drop_ids"].split(","))),
            tuple(map(int, row["add_ids"].split(","))),
        )
    assert actual == expected
    assert summary["candidates"] == len(expected) == len(list(output.glob("candidate-*.txt")))
    for distance, shell in enumerate(summary["shells"], 1):
        assert shell["complete"] and shell["deletions"] == math.comb(len(original), distance)
        assert shell["candidates"] == sum(row[0] == distance for row in expected.values())
    witness_inventory = [(path.name, sha(path)) for path in sorted(output.glob("candidate-*.txt"))]
    return {
        "fixture_ids": fixture_ids,
        "initial_holes": holes,
        "unpruned_oracle_tuples": tuples,
        "candidate_count": len(expected),
        "native": summary,
        "exact_sets_match": True,
        "input_path": str(source.relative_to(ROOT)),
        "input_sha256": sha(source),
        "output_path": str(output.relative_to(ROOT)),
        "ledger_sha256": sha(output / "candidates.tsv"),
        "witness_inventory_sha256": hashlib.sha256(
            json.dumps(witness_inventory, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def main():
    assert sha(INPUT) == INPUT_SHA
    assert not RAW.exists(), "preparation is create-only"
    RAW.mkdir(parents=True)
    binary = RAW / "search"
    command = [
        "clang++",
        "-O3",
        "-std=c++17",
        "-Wall",
        "-Wextra",
        "-Werror",
        str(HERE / "search.cpp"),
        "-o",
        str(binary),
    ]
    compiled = subprocess.run(command, capture_output=True, text=True, check=True)
    (RAW / "compiler-stdout.txt").write_text(compiled.stdout)
    (RAW / "compiler-stderr.txt").write_text(compiled.stderr)
    version = subprocess.run(["clang++", "--version"], capture_output=True, text=True, check=True)
    (RAW / "compiler-version.txt").write_text(version.stdout)
    fixtures = [
        fixture_check(binary, ids, index)
        for index, ids in enumerate(([0, 1, 2, 3], [0, 1, 4, 9, 20], [0, 1, 3, 6, 10]))
    ]
    original = INPUT.read_text().splitlines()
    damaged = {
        "duplicate": [original[0], *original[1:-1], original[0]],
        "short-row": [" ".join(original[0].split()[:-1]), *original[1:]],
        "long-row": [original[0] + " 17", *original[1:]],
        "label-zero": ["0 " + " ".join(original[0].split()[1:]), *original[1:]],
        "label-seventeen": [*original[:-1], " ".join(original[-1].split()[:-1]) + " 17"],
        "unsorted-labels": [" ".join(reversed(original[0].split())), *original[1:]],
        "unsorted-family": [original[1], original[0], *original[2:]],
        "malformed-label": ["x " + " ".join(original[0].split()[1:]), *original[1:]],
        "missing-block": original[:-1],
        "extra-block": [*original, original[-1]],
        "blank-row": [original[0], "", *original[1:]],
    }
    rejected = []
    for name, lines in damaged.items():
        path = RAW / f"damaged-{name}.txt"
        path.write_text("\n".join(lines) + "\n")
        output, process = invoke(binary, path, 6, 6, f"reject-{name}", 1, 64)
        assert process.returncode == 2 and process.stderr.startswith("error:")
        assert not list(output.iterdir()) and not process.stdout
        rejected.append(name)
    for name, holes, target, seconds in [
        ("nan-seconds", 6, 6, "nan"),
        ("infinite-seconds", 6, 6, "inf"),
        ("negative-seconds", 6, 6, -1),
        ("over-budget", 6, 6, 31),
        ("wrong-holes", 7, 6, 1),
        ("non-neutral-target", 6, 5, 1),
    ]:
        output, process = invoke(binary, INPUT, holes, target, f"reject-{name}", seconds, 64)
        assert process.returncode == 2 and process.stderr.startswith("error:")
        assert not list(output.iterdir()) and not process.stdout
        rejected.append(name)
    output, process = invoke(binary, INPUT, 6, 6, "zero-budget", 0, 64)
    assert process.returncode == 0 and not process.stderr
    zero = json.loads(process.stdout)
    assert zero["status"] == "timeout" and zero["candidates"] == 0
    assert all(not s["complete"] and s["deletions"] == s["tuples"] == 0 for s in zero["shells"])
    assert (
        output / "candidates.tsv"
    ).read_text() == "candidate\tdistance\tholes\tdrop_ids\tadd_ids\n"
    # Process-control fixtures execute only tiny Python children, never the native search.
    spec = importlib.util.spec_from_file_location("neutral_driver_controls", HERE / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    watchdog_controls = []
    for name, script, seconds, grace, expected in [
        ("normal", "print('finished')", 2, 1, (False, False, False)),
        (
            "terminate",
            "import time; print('ready', flush=True); time.sleep(5)",
            1,
            1,
            (True, True, False),
        ),
        (
            "kill",
            "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); "
            "print('ready',flush=True); time.sleep(5)",
            1,
            0.1,
            (True, True, True),
        ),
    ]:
        observed = runner.execute_bounded([sys.executable, "-c", script], seconds, grace)
        assert tuple(observed[k] for k in ("watchdog", "terminated", "killed")) == expected
        assert not observed["stderr"]
        assert ("finished" if name == "normal" else "ready") in observed["stdout"]
        watchdog_controls.append({"name": name, **observed})
    controls = {
        "passed": True,
        "compile_command": command,
        "compiler_version": version.stdout,
        "source_sha256": sha(HERE / "search.cpp"),
        "binary_sha256": sha(binary),
        "fixtures": fixtures,
        "rejected_controls": rejected,
        "zero_budget": zero,
        "watchdog_controls": watchdog_controls,
        "production_replacement_tuples": 0,
        "production_search_launched": False,
    }
    dump(HERE / "controls.json", controls)
    inherited_path = HERE.parent / "native-h9-h10-reuse-pilot/manifest.json"
    inherited = json.loads(inherited_path.read_text())
    pins = {}
    for group in ("source_files", "input_files", "raw_files"):
        pins.update(inherited[group])
    for path in [
        HERE / "search.cpp",
        HERE / "run.py",
        HERE / "prepare.py",
        HERE / "controls.json",
        HERE / "README.md",
        binary,
        INPUT,
        inherited_path,
        HERE.parent / "native-h9-h10-reuse-pilot/run.py",
        HERE.parent / "h6-neutral-radius3-deletion-screen/receipt.json",
        HERE.parent / "h6-neutral-radius3-deletion-screen/replay.json",
        HERE.parent / "h6-neutral-radius3-deletion-screen/screen.cpp",
        HERE.parent / "h6-neutral-radius3-deletion-screen/run.py",
    ]:
        pins[str(path.relative_to(ROOT))] = sha(path)
    for relative, digest in pins.items():
        assert sha(ROOT / relative) == digest, f"inherited pin changed: {relative}"
    manifest = {
        "document": "H6 Neutral Radius-Three Pilot",
        "version": "v1.0.0",
        "status": "prepared; independent gate required; production unlaunched",
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "input_path": str(INPUT.relative_to(ROOT)),
        "input_sha256": INPUT_SHA,
        "binary_path": str(binary.relative_to(ROOT)),
        "pins": pins,
        "verifier_path": "experiments/2026-10-04/native-five-core-record-pilot/run.py",
        "classifier_path": "experiments/2026-10-04/native-h9-h10-reuse-pilot/run.py",
        "core_rows": inherited["core_rows"],
        "sixth_cap": inherited["sixth_cap"],
        "budget": {
            "native_seconds": 30,
            "watchdog_seconds": 35,
            "termination_grace_seconds": 5,
            "processes": 1,
            "runs": 1,
            "relaunch": False,
            "seed": None,
        },
        "target_holes": 6,
        "distances": [1, 2, 3],
        "deletion_counts": [64, 2016, 41664],
        "eligible_adders": "all4304 pentads outside the entire original64-block family",
        "stopping": "Natural exhaustion or budget; retain every H<=6 candidate. "
        "All persisted candidates are dual-verified after the native process.",
        "search_filters": "Coverage only: top-k sum bound and necessary individual-count floor.",
        "scope": "Complete only if all three exact-distance shells finish. Pair, weak, and "
        "six named caps are postclassification only. No unrestricted lower-bound claim.",
        "production_search_launched": False,
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "passed": True,
                "fixture_candidates": [row["candidate_count"] for row in fixtures],
                "rejected_controls": len(rejected),
                "manifest_sha256": sha(HERE / "manifest.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
