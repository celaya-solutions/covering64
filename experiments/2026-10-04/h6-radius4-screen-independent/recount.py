# Document:    Independent H6 Four-Deletion Recount Driver
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      072cbbee15697d1c7d75b578192a657ac1ff61e3541766b71e192a64219928bc
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""One bounded deletion-only audit; saves full rows and directly checks every survivor."""

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
PRODUCER = HERE.parent / "h6-radius4-deletion-upper-screen"
RAW = ROOT / "experiments/scratch/h6-radius4-screen-independent-20261004"
RECEIPT_SHA = "d9b9ff8db84089e8f32201e4e826d298ec5c67f1c1bbc323058b1f89adb13107"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    assert sha(PRODUCER / "receipt.json") == RECEIPT_SHA
    producer = json.loads((PRODUCER / "receipt.json").read_text())
    assert sha(PRODUCER / "screen.cpp") == producer["source_sha256"]
    assert sha(producer["command"][0]) == producer["binary_sha256"]
    input_path = Path(producer["command"][1])
    assert sha(input_path) == producer["input_sha256"]
    assert producer["summary"]["complete"] and not producer["watchdog_fired"]
    assert not RAW.exists(), "create-only audit"
    RAW.mkdir(parents=True)
    binary = RAW / "check"
    command = [
        "clang++",
        "-O3",
        "-std=c++17",
        "-Wall",
        "-Wextra",
        "-Werror",
        str(HERE / "check.cpp"),
        "-o",
        str(binary),
    ]
    compiled = subprocess.run(command, capture_output=True, text=True, check=True)
    (RAW / "compiler-stdout.txt").write_text(compiled.stdout)
    (RAW / "compiler-stderr.txt").write_text(compiled.stderr)
    rows_path = RAW / "deletions.tsv"
    started = time.monotonic()
    process = subprocess.run(
        [str(binary), str(input_path), str(rows_path)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    wall = time.monotonic() - started
    (RAW / "stdout.json").write_text(process.stdout)
    (RAW / "stderr.txt").write_text(process.stderr)
    assert process.returncode == 0 and not process.stderr
    result = json.loads(process.stdout)
    native_receipt = {
        "source_sha256": sha(HERE / "check.cpp"),
        "binary_sha256": sha(binary),
        "compile_command": command,
        "native": result,
        "wall_seconds": wall,
        "producer_receipt_sha256": RECEIPT_SHA,
        "raw_files": {str(p.relative_to(ROOT)): sha(p) for p in RAW.iterdir() if p.is_file()},
    }
    dump(HERE / "native-recount.json", native_receipt)
    assert result["complete"], "audit hit its cap; retain partial receipt, no complete claim"
    for key, value in result.items():
        if key != "seconds":
            assert producer["summary"][key] == value, key
    blocks = list(itertools.combinations(range(1, 17), 5))
    triples = list(itertools.combinations(range(1, 17), 3))
    rank = {block: i for i, block in enumerate(blocks)}
    trank = {triple: i for i, triple in enumerate(triples)}
    masks = [sum(1 << trank[t] for t in itertools.combinations(b, 3)) for b in blocks]
    family = [tuple(map(int, line.split())) for line in input_path.read_text().splitlines()]
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
    holes_hist, pool_hist, floor_hist = Counter(), Counter(), Counter()
    pool_tuples, direct_rows, samples, survivors, excluded, completed = 0, 0, 0, 0, 0, 0
    large_pools = []
    with rows_path.open() as handle:
        rows = csv.DictReader(handle, delimiter="\t")
        for index, (raw, expected) in enumerate(
            zip(rows, itertools.combinations(selected, 4), strict=True)
        ):
            row = {k: int(v) for k, v in raw.items()}
            dropped = tuple(row[f"delete{i}"] for i in range(4))
            assert dropped == expected
            u = owner_masks[()]
            for size in (1, 2, 3):
                for owner in itertools.combinations(dropped, size):
                    u |= owner_masks.get(owner, 0)
            missing = u.bit_count()
            assert missing == row["uncovered"] and row["demand"] == missing - 5
            completed += 1
            holes_hist[missing] += 1
            assert row["excluded"] in (0, 1)
            excluded += row["excluded"]
            if not row["excluded"]:
                survivors += 1
                pool_hist[row["pool"]] += 1
                floor_hist[row["floor"]] += 1
                pool_tuples += math.comb(row["pool"], 4)
                if row["pool"] >= 177:
                    large_pools.append({"dropped": dropped, "pool": row["pool"]})
            sampled = bool(row["excluded"] and index % 5003 == 0)
            if row["excluded"] and not sampled:
                continue
            direct_rows += 1
            samples += sampled
            scores = [(masks[bid] & u).bit_count() for bid in eligible]
            top = sorted(scores, reverse=True)[:4]
            upper = sum(top)
            floor = max(0, row["demand"] - sum(top[:3]))
            assert top == [row[f"top{i}"] for i in range(4)]
            assert upper == row["upper"] and int(upper < row["demand"]) == row["excluded"]
            assert floor == row["floor"]
            assert sum(score >= floor for score in scores) == row["pool"]
    assert completed == result["completed_deletions"] == math.comb(64, 4)
    assert (excluded, survivors, pool_tuples) == (
        result["excluded"],
        result["survivors"],
        result["replacement_tuples_upper"],
    )
    for actual, key in [
        (holes_hist, "residual_hole_histogram"),
        (pool_hist, "pool_histogram"),
        (floor_hist, "floor_histogram"),
    ]:
        assert {str(k): v for k, v in sorted(actual.items())} == result[key]
    audit = {
        "passed": True,
        "checker_sha256": sha(__file__),
        "producer_receipt_sha256": RECEIPT_SHA,
        "native_recount_sha256": sha(HERE / "native-recount.json"),
        "deletion_rows_recounted_twice": completed,
        "full_universe_native_adder_score_rows": completed,
        "direct_python_adder_score_rows": direct_rows,
        "all_survivor_pools_directly_recounted": survivors,
        "excluded_rows_additionally_sampled_in_python": samples,
        "replacement_tuples_enumerated": 0,
        "necessary_addition_quadruples": pool_tuples,
        "largest_pools": large_pools,
        "pool364_tuple_contribution": 4 * math.comb(364, 4),
        "pool177_178_tuple_contribution": 8 * (math.comb(177, 4) + math.comb(178, 4)),
        "scope": "Full independent deletion-only recount rebuilds scores from original "
        "triple owners for every deletion. Python recounts every deletion's uncovered "
        "triples and directly checks all survivor pools plus sampled exclusions. "
        "No addition tuple is examined. The3.7billion necessary tuples do not establish "
        "that unpruned exact-distance4 replacement enumeration fits60seconds.",
    }
    dump(HERE / "audit.json", audit)
    print(
        json.dumps(
            {
                k: audit[k]
                for k in (
                    "passed",
                    "deletion_rows_recounted_twice",
                    "all_survivor_pools_directly_recounted",
                    "necessary_addition_quadruples",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
