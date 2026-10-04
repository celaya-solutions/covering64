# Document:    H6 Neutral Radius-Three Deletion Screen Driver and Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      f289091fa0771f19c1f6c30439205cad3dbf2e126a4419a091104205407f3f54
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""One root-authorized deletion-only screen; no replacement tuple search."""

import csv
import hashlib
import itertools
import json
import math
import subprocess
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/h6-neutral-radius3-deletion-screen-20261004"
INPUT = HERE.parent / "native-h9-h10-reuse-pilot/seed-2026105901/search-final-raw64.txt"
INPUT_SHA = "2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def recount(summary, rows_path):
    blocks = list(itertools.combinations(range(1, 17), 5))
    triples = list(itertools.combinations(range(1, 17), 3))
    rank = {block: i for i, block in enumerate(blocks)}
    trank = {triple: i for i, triple in enumerate(triples)}
    masks = [sum(1 << trank[t] for t in itertools.combinations(b, 3)) for b in blocks]
    family = [tuple(map(int, line.split())) for line in INPUT.read_text().splitlines()]
    selected = [rank[b] for b in family]
    eligible = sorted(set(range(4368)) - set(selected))
    owners = [[] for _ in triples]
    for bid, block in zip(selected, family, strict=True):
        for triple in itertools.combinations(block, 3):
            owners[trank[triple]].append(bid)
    owner_masks = {}
    for triple, owner in enumerate(owners):
        key = tuple(owner)
        owner_masks[key] = owner_masks.get(key, 0) | (1 << triple)
    assert owner_masks[()].bit_count() == 6
    totals = []
    with rows_path.open() as handle:
        reader = iter(csv.DictReader(handle, delimiter="\t"))
        for distance, shell in enumerate(summary["shells"], 1):
            pools, floors, holes = Counter(), Counter(), Counter()
            excluded = survivors = tuples = scored_rows = sampled_exclusions = 0
            for index, dropped in enumerate(itertools.combinations(selected, distance)):
                raw = next(reader)
                actual_drop = tuple(map(int, raw.pop("drop_ids").split(",")))
                row = {key: int(value) for key, value in raw.items()}
                assert row["distance"] == distance and actual_drop == dropped
                mask = owner_masks[()]
                for size in range(1, distance + 1):
                    for owner in itertools.combinations(dropped, size):
                        mask |= owner_masks.get(owner, 0)
                missing = mask.bit_count()
                assert missing == row["uncovered"] and row["demand"] == missing - 6
                holes[missing] += 1
                assert row["excluded"] in (0, 1)
                excluded += row["excluded"]
                necessary = 0 if row["excluded"] else math.comb(row["pool"], distance)
                assert row["necessary_tuples"] == necessary
                tuples += necessary
                if not row["excluded"]:
                    survivors += 1
                    pools[row["pool"]] += 1
                    floors[row["floor"]] += 1
                sampled = bool(row["excluded"] and index % 503 == 0)
                if row["excluded"] and not sampled:
                    continue
                scored_rows += 1
                sampled_exclusions += sampled
                scores = [(masks[bid] & mask).bit_count() for bid in eligible]
                top = sorted(scores, reverse=True)[:distance]
                upper = sum(top)
                floor = max(0, row["demand"] - sum(top[:-1]))
                assert top + [0] * (3 - distance) == [row[f"top{i}"] for i in range(3)]
                assert upper == row["upper"] and int(upper < row["demand"]) == row["excluded"]
                assert floor == row["floor"] and sum(s >= floor for s in scores) == row["pool"]
            assert shell["complete"] and shell["deletions"] == math.comb(64, distance)
            assert (excluded, survivors, tuples) == (
                shell["excluded"],
                shell["survivors"],
                shell["necessary_tuples"],
            )
            assert excluded + survivors == shell["deletions"]
            for actual, key in [
                (pools, "pool_histogram"),
                (floors, "floor_histogram"),
                (holes, "residual_hole_histogram"),
            ]:
                assert {str(k): v for k, v in sorted(actual.items())} == shell[key]
            totals.append(
                {
                    "distance": distance,
                    "all_uncovered_rows_recounted": shell["deletions"],
                    "all_survivor_pools_directly_recounted": survivors,
                    "sampled_exclusion_scores_recounted": sampled_exclusions,
                    "direct_adder_score_rows": scored_rows,
                    "necessary_tuples": tuples,
                }
            )
        assert next(reader, None) is None
    return totals


def main():
    assert not RAW.exists() and not (HERE / "receipt.json").exists(), "create-only; no relaunch"
    assert sha(INPUT) == INPUT_SHA
    RAW.mkdir(parents=True)
    binary = RAW / "screen"
    compile_command = [
        "clang++",
        "-O3",
        "-std=c++17",
        "-Wall",
        "-Wextra",
        "-Werror",
        str(HERE / "screen.cpp"),
        "-o",
        str(binary),
    ]
    compiled = subprocess.run(compile_command, capture_output=True, text=True, check=True)
    (RAW / "compile-stdout.txt").write_text(compiled.stdout)
    (RAW / "compile-stderr.txt").write_text(compiled.stderr)
    compiler = subprocess.check_output(["clang++", "--version"], text=True)
    (RAW / "compiler-version.txt").write_text(compiler)
    original = INPUT.read_text().splitlines()
    invalid = {
        "duplicate": [original[0], original[0], *original[2:]],
        "short": [*original[:-1]],
        "extra-label": [original[0] + " 17", *original[1:]],
        "malformed": ["invalid", *original[1:]],
        "label-range": ["0 1 2 3 4", *original[1:]],
        "order": [original[1], original[0], *original[2:]],
    }
    controls = []
    for name, lines in invalid.items():
        path = RAW / f"invalid-{name}.txt"
        path.write_text("\n".join(lines) + "\n")
        output = RAW / f"invalid-{name}-rows.tsv"
        process = subprocess.run(
            [str(binary), str(path), str(output)], capture_output=True, text=True, timeout=5
        )
        assert (
            process.returncode == 2
            and process.stderr
            and not process.stdout
            and not output.exists()
        )
        controls.append(name)
    rows_path = RAW / "deletions.tsv"
    command = [str(binary), str(INPUT), str(rows_path)]
    started = time.monotonic()
    watchdog = False
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
        stdout, stderr, returncode = process.stdout, process.stderr, process.returncode
    except subprocess.TimeoutExpired as error:
        watchdog = True
        stdout, stderr, returncode = error.stdout or b"", error.stderr or b"", None
        stdout = stdout.decode() if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode() if isinstance(stderr, bytes) else stderr
    wall = time.monotonic() - started
    (RAW / "stdout.json").write_text(stdout)
    (RAW / "stderr.txt").write_text(stderr)
    summary = json.loads(stdout) if returncode == 0 and not stderr else None
    receipt = {
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": sha(HERE / "screen.cpp"),
        "driver_sha256": sha(__file__),
        "binary_sha256": sha(binary),
        "input_sha256": INPUT_SHA,
        "command": command,
        "compile_command": compile_command,
        "compiler": compiler,
        "controls_rejected": controls,
        "internal_seconds": 28,
        "watchdog_seconds": 30,
        "wall_seconds": wall,
        "watchdog_fired": watchdog,
        "returncode": returncode,
        "summary": summary,
        "production_screen_calls": 1,
        "replacement_tuples_enumerated": 0,
        "optimizer_calls": 0,
        "raw_files": {str(p.relative_to(ROOT)): sha(p) for p in RAW.iterdir() if p.is_file()},
        "scope": "Deletion-only coverage workload for exact replacement distances1,2,3 "
        "from the pinned rawH6 family, targetH<=6. No pair/weak/core restrictions. "
        "No replacement tuple enumeration or full-search preparation/launch.",
    }
    dump(HERE / "receipt.json", receipt)
    assert not watchdog and returncode == 0 and not stderr and summary["complete"]
    replay = {
        "passed": True,
        "receipt_sha256": sha(HERE / "receipt.json"),
        "checker_sha256": sha(__file__),
        "rows_sha256": sha(rows_path),
        "shells": recount(summary, rows_path),
        "replacement_tuples_enumerated": 0,
        "scope": "Every deletion/U row independently recounted from owner subsets; "
        "all survivor pools and deterministic excluded samples directly scored using560bit "
        "block/triple intersections. Not a replacement search or weak-feasibility result.",
    }
    dump(HERE / "replay.json", replay)
    print(
        json.dumps(
            {
                "complete": True,
                "shells": [
                    {
                        k: shell[k]
                        for k in (
                            "distance",
                            "deletions",
                            "excluded",
                            "survivors",
                            "necessary_tuples",
                            "minimum_pool",
                            "maximum_pool",
                        )
                    }
                    for shell in summary["shells"]
                ],
                "seconds": summary["seconds"],
                "replacement_tuples_enumerated": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
