# Document:    H6 Radius Four Prefix Preparation and Fixture Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      78d0c0839d2b640c81aa66e22d44f08fd511e0677a8440f8e923f707df33b4ff
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Compile and check only small v7 fixtures; never explore the actual H6 neighborhood."""

import csv
import hashlib
import itertools
import json
import math
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/h6-strict-hole-radius4-prefix-pilot-20261004"
INPUT = HERE.parent / "native-h9-h10-reuse-pilot/seed-2026105901/search-final-raw64.txt"
INPUT_SHA = "2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855"
BLOCKS = list(itertools.combinations(range(1, 8), 5))
TRIPLES = set(itertools.combinations(range(1, 8), 3))
COVERS = [set(itertools.combinations(b, 3)) for b in BLOCKS]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def hole_count(ids):
    return len(TRIPLES - set().union(*(COVERS[i] for i in ids)))


def write_family(path, ids):
    path.write_text("".join(" ".join(map(str, BLOCKS[i])) + "\n" for i in sorted(ids)))


def invoke(binary, source, expected, name, count, seconds="10"):
    output = RAW / name
    output.mkdir()
    command = [
        str(binary),
        str(source),
        str(expected),
        str(expected - 1),
        str(output),
        seconds,
        str(count),
        "--fixture-v",
        "7",
    ]
    process = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
    (RAW / f"{name}-stdout.json").write_text(process.stdout)
    (RAW / f"{name}-stderr.txt").write_text(process.stderr)
    return process, output, command


def fixture(binary, ids, index):
    source = RAW / f"fixture-{index}.txt"
    write_family(source, ids)
    expected = hole_count(ids)
    complement = sorted(set(range(21)) - set(ids))
    oracle = {}
    tested = 0
    for drop in itertools.combinations(ids, 4):
        retained = set(ids) - set(drop)
        for add in itertools.combinations(complement, 4):
            tested += 1
            candidate = tuple(sorted(retained | set(add)))
            holes = hole_count(candidate)
            if holes < expected:
                assert candidate not in oracle
                oracle[candidate] = {"holes": holes, "drop": list(drop), "add": list(add)}
    process, output, command = invoke(binary, source, expected, f"fixture-{index}-run", len(ids))
    assert process.returncode == 0 and not process.stderr
    summary = json.loads(process.stdout)
    assert summary["status"] == "complete" and len(summary["shells"]) == 1
    shell = summary["shells"][0]
    assert shell["distance"] == 4 and shell["complete"]
    assert shell["deletions"] == math.comb(len(ids), 4)
    rows = list(csv.DictReader((output / "candidates.tsv").open(), delimiter="\t"))
    assert [int(r["candidate"]) for r in rows] == list(range(1, len(rows) + 1))
    actual = {}
    for row in rows:
        path = output / f"candidate-{row['candidate']}.txt"
        blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
        assert blocks == sorted(set(blocks)) and len(blocks) == len(ids)
        candidate = tuple(BLOCKS.index(block) for block in blocks)
        assert candidate not in actual
        assert int(row["distance"]) == 4
        drop = sorted(set(ids) - set(candidate))
        add = sorted(set(candidate) - set(ids))
        assert len(drop) == len(add) == 4
        assert drop == list(map(int, row["drop_ids"].split(",")))
        assert add == list(map(int, row["add_ids"].split(",")))
        holes = hole_count(candidate)
        assert holes == int(row["holes"]) < expected
        actual[candidate] = {"holes": holes, "drop": drop, "add": add}
    assert actual == oracle
    assert summary["candidates"] == shell["candidates"] == len(oracle)
    assert len(list(output.glob("candidate-*.txt"))) == len(oracle)
    return {
        "ids": list(ids),
        "holes": expected,
        "oracle_tuples": tested,
        "oracle_candidates": len(oracle),
        "native_summary": summary,
        "command": command,
        "input_sha256": sha(source),
        "ledger_sha256": sha(output / "candidates.tsv"),
    }


def main():
    assert not RAW.exists() and not (HERE / "manifest.json").exists()
    assert sha(INPUT) == INPUT_SHA
    RAW.mkdir(parents=True)
    binary = RAW / "search"
    command = [
        "/usr/bin/clang++",
        "-std=c++17",
        "-O3",
        "-Wall",
        "-Wextra",
        "-pedantic",
        str(HERE / "search.cpp"),
        "-o",
        str(binary),
    ]
    built = subprocess.run(command, capture_output=True, text=True, check=False)
    (RAW / "compile.stdout").write_text(built.stdout)
    (RAW / "compile.stderr").write_text(built.stderr)
    assert built.returncode == 0 and not built.stderr
    fixtures = [
        fixture(binary, ids, index)
        for index, ids in enumerate(((0, 1, 2, 3), (0, 1, 9, 20), (0, 1, 4, 9, 20)), 1)
    ]
    assert [f["oracle_candidates"] for f in fixtures] == [1554, 0, 43]
    source = RAW / "fixture-1.txt"
    process, output, zero_command = invoke(binary, source, 10, "zero-budget", 4, "0")
    assert process.returncode == 0 and not process.stderr
    zero = json.loads(process.stdout)
    assert zero["status"] == "timeout" and zero["candidates"] == 0
    assert not zero["shells"][0]["complete"] and zero["shells"][0]["deletions"] == 0
    assert list(csv.DictReader((output / "candidates.tsv").open(), delimiter="\t")) == []
    rejected = []
    original = source.read_text().splitlines()
    damages = {
        "duplicate": [original[0], original[0], *original[2:]],
        "unsorted": list(reversed(original)),
        "out-of-range": ["1 2 3 4 8", *original[1:]],
        "extra-label": [original[0] + " 7", *original[1:]],
        "malformed": ["not a block", *original[1:]],
    }
    for name, lines in damages.items():
        path = RAW / f"damaged-{name}.txt"
        path.write_text("\n".join(lines) + "\n")
        process, _, _ = invoke(binary, path, 10, f"reject-{name}", 4)
        assert process.returncode == 2 and process.stderr and not process.stdout
        rejected.append(name)
    for name, expected, seconds in (("wrong-holes", 9, "10"), ("nan-budget", 10, "nan")):
        process, _, _ = invoke(binary, source, expected, f"reject-{name}", 4, seconds)
        assert process.returncode == 2 and process.stderr and not process.stdout
        rejected.append(name)
    controls = {
        "passed": True,
        "source_sha256": sha(HERE / "search.cpp"),
        "binary_sha256": sha(binary),
        "fixtures": fixtures,
        "rejected_controls": rejected,
        "zero_budget": zero,
        "zero_budget_command": zero_command,
        "production_prefixes_explored": 0,
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
        HERE.parent / "h6-strict-hole-radius3-pilot/search.cpp",
        HERE.parent / "h6-strict-hole-radius3-pilot/run.py",
        HERE.parent / "h6-strict-hole-radius3-pilot/result.json",
        HERE.parent / "h6-radius4-deletion-upper-screen/screen.cpp",
        HERE.parent / "h6-radius4-deletion-upper-screen/receipt.json",
        HERE.parent / "h6-radius4-screen-independent/audit.json",
    ]:
        pins[str(path.relative_to(ROOT))] = sha(path)
    for relative, digest in pins.items():
        assert sha(ROOT / relative) == digest, relative
    manifest = {
        "document": "H6 Strict-Hole Radius Four Prefix Pilot",
        "version": "v1.0.0",
        "status": "prepared; independent gate required; production unlaunched",
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "input_path": str(INPUT.relative_to(ROOT)),
        "input_sha256": INPUT_SHA,
        "binary_path": str(binary.relative_to(ROOT)),
        "pins": pins,
        "compiler": subprocess.check_output(["/usr/bin/clang++", "--version"], text=True),
        "compile_command": command,
        "verifier_path": "experiments/2026-10-04/native-five-core-record-pilot/run.py",
        "classifier_path": "experiments/2026-10-04/native-h9-h10-reuse-pilot/run.py",
        "core_rows": inherited["core_rows"],
        "sixth_cap": inherited["sixth_cap"],
        "budget": {
            "native_seconds": 59,
            "watchdog_seconds": 60,
            "processes": 1,
            "runs": 1,
            "relaunch": False,
            "seed": None,
        },
        "target_holes": 5,
        "distances": [4],
        "deletion_counts": [635376],
        "eligible_adders": "All 4304 pentads outside the entire original 64-block family.",
        "stopping": "Natural exhaustion or budget; all candidates persist before dual validation.",
        "search_filters": "Top-four deletion score bound and necessary individual floor; then "
        "at each ordered addition prefix, recomputed residual gains, top-remaining gain bound, "
        "and necessary tail floor. Masks give exact union coverage at complete tuples.",
        "complexity_upper": {
            "unfiltered_two_prefixes": 1012567,
            "unfiltered_depth2_tail_gain_popcounts": 56485156,
            "naive_complete_tuples": 3697940975,
        },
        "scope": "Exact distance four only. No repeat of distances one through three. "
        "Complete only if the single shell finishes; timeout is inconclusive. Pair, weak, "
        "and six named caps are postclassification only. No global lower-bound claim.",
        "production_prefixes_explored": 0,
        "production_search_launched": False,
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "prepared": True,
                "fixture_candidates": [1554, 0, 43],
                "production_prefixes_explored": 0,
                "manifest_sha256": sha(HERE / "manifest.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
