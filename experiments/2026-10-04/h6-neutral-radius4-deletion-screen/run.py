# Document:    H6 Neutral Four-Deletion Screen and Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      749ba8488cb23150ab5b2f76d7a04c6834e7782c5405c9be55aae3079e9d9fc3
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""One authorized30s deletion-only screen, with no addition tuples or prefixes."""

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
RAW = ROOT / "experiments/scratch/h6-neutral-radius4-deletion-screen-20261004"
INPUT = HERE.parent / "native-h9-h10-reuse-pilot/seed-2026105901/search-final-raw64.txt"
INPUT_SHA = "2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855"
BASE = HERE.parent / "h6-radius4-screen-independent/check.cpp"
BASE_SHA = "5e0827768741fa5a3eed32c667f42f1bc291dcca15d61838cd619545f0af97b8"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    assert sha(BASE) == BASE_SHA and sha(INPUT) == INPUT_SHA
    before = "\n".join(BASE.read_text().split("\n")[10:])
    after = "\n".join((HERE / "screen.cpp").read_text().split("\n")[10:])
    assert before.count("demand=missing-5") == 1
    assert after == before.replace("demand=missing-5", "demand=missing-6")
    assert math.comb(64, 4) * math.comb(4304, 4) < 2**64
    assert not RAW.exists() and not (HERE / "receipt.json").exists()
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
    built = subprocess.run(compile_command, capture_output=True, text=True, check=True)
    (RAW / "compile-stdout.txt").write_text(built.stdout)
    (RAW / "compile-stderr.txt").write_text(built.stderr)
    compiler = subprocess.check_output(["clang++", "--version"], text=True)
    (RAW / "compiler-version.txt").write_text(compiler)
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
        "base_source_sha256": BASE_SHA,
        "only_body_change": "demand=missing-5 to demand=missing-6",
        "binary_sha256": sha(binary),
        "input_sha256": INPUT_SHA,
        "compile_command": compile_command,
        "compiler": compiler,
        "command": command,
        "internal_seconds": 28,
        "watchdog_seconds": 30,
        "wall_seconds": wall,
        "returncode": returncode,
        "watchdog_fired": watchdog,
        "summary": summary,
        "production_screen_calls": 1,
        "replacement_tuples_enumerated": 0,
        "prefixes_explored": 0,
        "raw_files": {str(p.relative_to(ROOT)): sha(p) for p in RAW.iterdir() if p.is_file()},
    }
    dump(HERE / "receipt.json", receipt)
    assert not watchdog and returncode == 0 and not stderr and summary["complete"]
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
    assert owner_masks[()].bit_count() == 6 and max(map(len, owner_masks)) == 3
    pools, floors, holes = Counter(), Counter(), Counter()
    tuples = survivors = excluded = direct_rows = sampled_exclusions = completed = 0
    with rows_path.open() as handle:
        rows = csv.DictReader(handle, delimiter="\t")
        for index, (raw, expected) in enumerate(
            zip(rows, itertools.combinations(selected, 4), strict=True)
        ):
            row = {k: int(v) for k, v in raw.items()}
            dropped = tuple(row[f"delete{i}"] for i in range(4))
            assert dropped == expected
            mask = owner_masks[()]
            for size in (1, 2, 3):
                for owner in itertools.combinations(dropped, size):
                    mask |= owner_masks.get(owner, 0)
            missing = mask.bit_count()
            assert missing == row["uncovered"] and row["demand"] == missing - 6
            completed += 1
            holes[missing] += 1
            excluded += row["excluded"]
            if not row["excluded"]:
                survivors += 1
                pools[row["pool"]] += 1
                floors[row["floor"]] += 1
                tuples += math.comb(row["pool"], 4)
            sampled = bool(row["excluded"] and index % 5003 == 0)
            if row["excluded"] and not sampled:
                continue
            direct_rows += 1
            sampled_exclusions += sampled
            scores = [(masks[bid] & mask).bit_count() for bid in eligible]
            top = sorted(scores, reverse=True)[:4]
            upper = sum(top)
            floor = max(0, row["demand"] - sum(top[:3]))
            assert top == [row[f"top{i}"] for i in range(4)]
            assert upper == row["upper"] and int(upper < row["demand"]) == row["excluded"]
            assert floor == row["floor"] and sum(s >= floor for s in scores) == row["pool"]
    assert completed == summary["completed_deletions"] == math.comb(64, 4)
    assert (excluded, survivors, tuples) == (
        summary["excluded"],
        summary["survivors"],
        summary["replacement_tuples_upper"],
    )
    for actual, key in [
        (pools, "pool_histogram"),
        (floors, "floor_histogram"),
        (holes, "residual_hole_histogram"),
    ]:
        assert {str(k): v for k, v in sorted(actual.items())} == summary[key]
    replay = {
        "passed": True,
        "receipt_sha256": sha(HERE / "receipt.json"),
        "checker_sha256": sha(__file__),
        "deletion_rows_recounted": completed,
        "all_survivor_pools_directly_recounted": survivors,
        "sampled_exclusion_scores_recounted": sampled_exclusions,
        "direct_adder_score_rows": direct_rows,
        "necessary_addition_quadruples": tuples,
        "prefixes_explored": 0,
        "replacement_tuples_enumerated": 0,
        "endpoint_count_upper_bound_from_screen": tuples,
        "scope": "All deletion/uncovered rows and survivor pools checked; no replacement "
        "or prefix explored. Necessary tuple count is a loose endpoint/output ceiling, "
        "not a measured candidate count or a runtime promise.",
    }
    dump(HERE / "replay.json", replay)
    print(
        json.dumps(
            {
                k: summary[k]
                for k in (
                    "complete",
                    "seconds",
                    "completed_deletions",
                    "excluded",
                    "survivors",
                    "minimum_pool",
                    "maximum_pool",
                    "replacement_tuples_upper",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
