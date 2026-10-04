# Document:    Independent Radius-Three Enumerator Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      be63f0e0f10c9016d2729969a6bdee6814695344b170dd7710f805d54457cf4a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Compare fixture-mode outputs with unpruned set enumeration, never production."""

import hashlib
import itertools
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/h6-radius3-root-controls-20261004"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    binary = Path(sys.argv[1]).resolve()
    RAW.mkdir(parents=True, exist_ok=False)
    blocks = list(itertools.combinations(range(1, 8), 5))
    cover = [set(itertools.combinations(block, 3)) for block in blocks]
    universe = set(itertools.combinations(range(1, 8), 3))
    initial = (0, 8, 20)
    outside = [i for i in range(21) if i not in initial]
    expected_holes = len(universe - set.union(*(cover[i] for i in initial)))
    target = expected_holes - 1
    source = RAW / "fixture.txt"
    source.write_text("".join(" ".join(map(str, blocks[i])) + "\n" for i in initial))
    expected = set()
    shell_counts = []
    for distance in (1, 2, 3):
        seen = 0
        for dropped in itertools.combinations(initial, distance):
            kept = set(initial) - set(dropped)
            for added in itertools.combinations(outside, distance):
                seen += 1
                family = tuple(sorted(kept | set(added)))
                holes = len(universe - set.union(*(cover[i] for i in family)))
                if holes <= target:
                    expected.add(family)
        shell_counts.append(seen)

    def invoke(name, path, seconds):
        output = RAW / name
        output.mkdir()
        command = [
            str(binary),
            str(path),
            str(expected_holes),
            str(target),
            str(output),
            str(seconds),
            "3",
            "--fixture-v",
            "7",
        ]
        run = subprocess.run(command, capture_output=True, text=True, timeout=15)
        (RAW / f"{name}.stdout").write_text(run.stdout)
        (RAW / f"{name}.stderr").write_text(run.stderr)
        return run, output

    run, output = invoke("complete", source, 10)
    assert run.returncode == 0, run.stderr
    summary = json.loads(run.stdout)
    assert summary["status"] == "complete"
    assert [row["deletions"] for row in summary["shells"]] == [3, 3, 1]
    assert all(row["complete"] for row in summary["shells"])
    actual = set()
    paths = list(output.glob("candidate-*.txt"))
    for path in paths:
        rows = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
        assert len(rows) == len(set(rows)) == 3
        family = tuple(blocks.index(row) for row in rows)
        assert family == tuple(sorted(family))
        assert len(universe - set.union(*(cover[i] for i in family))) <= target
        assert family not in actual
        actual.add(family)
    assert actual == expected
    assert summary["candidates"] == len(expected) == len(paths)
    assert len((output / "candidates.tsv").read_text().splitlines()) == len(paths) + 1

    stopped, _ = invoke("zero-budget", source, 0)
    stopped_summary = json.loads(stopped.stdout)
    assert stopped.returncode == 0 and stopped_summary["status"] == "timeout"
    assert stopped_summary["candidates"] == 0
    assert not any(row["complete"] for row in stopped_summary["shells"])

    damaged = {}
    lines = source.read_text().splitlines()
    for name, content in {
        "duplicate": "\n".join([lines[0], lines[0], lines[2]]) + "\n",
        "out-of-range": "0 2 3 4 5\n" + "\n".join(lines[1:]) + "\n",
        "fractional": lines[0].replace("1", "1.5", 1) + "\n" + "\n".join(lines[1:]) + "\n",
        "extra-label": lines[0] + " 7\n" + "\n".join(lines[1:]) + "\n",
    }.items():
        path = RAW / f"{name}.txt"
        path.write_text(content)
        bad, _ = invoke(name, path, 10)
        assert bad.returncode != 0
        damaged[name] = bad.returncode
    nonfinite, _ = invoke("nan-budget", source, "nan")
    assert nonfinite.returncode != 0
    result = {
        "passed": True,
        "binary_sha256": sha(binary),
        "checker_sha256": sha(__file__),
        "fixture_initial_ids": initial,
        "fixture_holes": expected_holes,
        "target": target,
        "unpruned_tuple_counts": shell_counts,
        "matching_candidates": len(expected),
        "native_summary": summary,
        "zero_budget_is_incomplete": True,
        "damaged_inputs": damaged,
        "nan_budget_rejected": True,
        "production_launches": 0,
        "scope": "Independent unpruned v7 fixture enumeration and failure controls only.",
    }
    (HERE / "controls.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
