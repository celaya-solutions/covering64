# Document:    Six Bounded Protected-Novelty Diversity Tests
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      61d9a419a0207ace0ad1abff50d2e5b14186941532e2c5384f487fa52f9b71cf
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare finite delta checks, then run only the authorized six 10-second cases."""

import argparse
import hashlib
import itertools
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from covering64.core import read_blocks, verify_cover, write_blocks

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/forced-novelty-20261004"
UNIVERSE = list(itertools.combinations(range(1, 17), 5))
IDS = {block: i for i, block in enumerate(UNIVERSE)}
TRIPLES = set(itertools.combinations(range(1, 17), 3))
SEEDS = {
    "A": (
        ROOT / "experiments/2026-10-04/point-star-repair/initial.txt",
        "d6dcfd2f1778f76c90ca67698865f683a44a6b69ddacad8f77cc4ee9021eacdf",
    ),
    "B": (
        ROOT / "experiments/2026-10-03/heavy-profile-neighborhood/improvement-h3.txt",
        "01a1442a14ecbe341f9035ce4b45cea6de4de7e5ceea6015873e4d0b35ed987f",
    ),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + "\n")


def missing(blocks):
    return sorted(
        TRIPLES - {triple for block in blocks for triple in itertools.combinations(block, 3)}
    )


def profile(blocks):
    counts = Counter(triple for block in blocks for triple in itertools.combinations(block, 3))
    heavy = sorted((triple, count) for triple, count in counts.items() if count >= 6)
    forbidden = [
        group
        for group in itertools.combinations(heavy, 5)
        if len({point for triple, _ in group for point in triple}) == 15
        and sum(count >= 7 for _, count in group) >= 2
    ]
    return {"heavy_triples": heavy, "forbidden_five_heavy_profile": bool(forbidden)}


def verify(path):
    blocks = list(read_blocks(path))
    assert len(blocks) == len(set(blocks)) == 64 and all(block in IDS for block in blocks)
    holes = missing(blocks)
    package = verify_cover(blocks)
    process = subprocess.run(
        [
            sys.executable,
            "-I",
            str(ROOT / "scripts/check_cover.py"),
            str(path),
            "--expected-blocks",
            "64",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode in (0, 1) and not process.stderr
    standalone = json.loads(process.stdout)
    assert package["uncovered"] == holes and standalone["uncovered"] == [list(t) for t in holes]
    assert package["canonical_sha256"] == standalone["canonical_sha256"] == sha(path)
    assert package["valid"] == standalone["valid"] == (not holes)
    assert process.returncode == (0 if not holes else 1)
    return {
        "path": str(Path(path).relative_to(ROOT)),
        "sha256": sha(path),
        "holes": len(holes),
        "uncovered": holes,
        "blocks": 64,
        "both_verifiers_agree": True,
        "cover": not holes,
        "profile": profile(blocks),
    }


def prepare():
    assert not RAW.exists() and not (HERE / "metadata.json").exists()
    RAW.mkdir()
    inputs = RAW / "inputs"
    inputs.mkdir()
    snapshots = [
        ROOT / "scripts/forced_novelty_heuristic.cpp",
        ROOT / "scripts/heuristic_search.cpp",
        Path(__file__),
    ]
    for source in snapshots:
        (inputs / source.name).write_bytes(source.read_bytes())
    starts = {}
    for label, (source, expected) in SEEDS.items():
        assert sha(source) == expected
        path = inputs / f"{label}.txt"
        path.write_bytes(source.read_bytes())
        starts[label] = list(read_blocks(path))
        assert len(starts[label]) == 64 and len(missing(starts[label])) == 3
    elite = set(starts["A"]) | set(starts["B"])
    assert len(elite) == 66 and len(set(starts["A"]) & set(starts["B"])) == 62
    write_blocks(inputs / "elite66.txt", sorted(elite))
    compiler = subprocess.check_output(["c++", "--version"], text=True)
    (inputs / "compiler-version.txt").write_text(compiler)
    binary = inputs / "novelty"
    command = [
        "c++",
        "-std=c++17",
        "-O3",
        "-Wall",
        "-Wextra",
        "-Werror",
        str(inputs / "forced_novelty_heuristic.cpp"),
        "-o",
        str(binary),
    ]
    process = subprocess.run(command, capture_output=True, text=True, check=False)
    dump(
        inputs / "compile.json",
        {
            "argv": command,
            "exit": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
        },
    )
    assert process.returncode == 0, process.stderr
    controls = []
    for label, blocks in starts.items():
        native = subprocess.run(
            [
                str(binary),
                "audit",
                str(inputs / f"{label}.txt"),
                str(inputs / "elite66.txt"),
                "8",
                "2026104900",
                "10",
                str(RAW / "unused"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert native.returncode == 0 and not native.stderr
        (RAW / f"{label}-delta-controls.jsonl").write_text(native.stdout)
        rows = [json.loads(line) for line in native.stdout.splitlines()]
        assert len(rows) == 512
        for row in rows:
            assert (
                row["old"] == IDS[blocks[row["slot"]]] and UNIVERSE[row["incoming"]] not in blocks
            )
            changed = blocks.copy()
            changed[row["slot"]] = UNIVERSE[row["incoming"]]
            assert row["before"] == len(missing(blocks))
            assert row["after"] == len(missing(changed))
            assert row["delta"] == row["after"] - row["before"]
        controls.append(
            {
                "seed_family": label,
                "fresh_delta_recounts": len(rows),
                "native_full_recounts_and_rollback_checks": len(rows),
                "start": verify(inputs / f"{label}.txt"),
            }
        )
    start_lines = (inputs / "A.txt").read_text().splitlines()
    damaged_inputs = {
        "duplicate": start_lines[:-1] + [start_lines[0]],
        "malformed-token": ["x " + start_lines[0]] + start_lines[1:],
        "out-of-range": ["0 " + start_lines[0]] + start_lines[1:],
        "wrong-cardinality": start_lines[:-1],
    }
    rejected_inputs = []
    for name, lines in damaged_inputs.items():
        bad = inputs / f"bad-{name}.txt"
        bad.write_text("\n".join(lines) + "\n")
        rejected = subprocess.run(
            [
                str(binary),
                "audit",
                str(bad),
                str(inputs / "elite66.txt"),
                "8",
                "2026104900",
                "10",
                str(RAW / "unused"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert rejected.returncode == 2 and not rejected.stdout
        rejected_inputs.append({"control": name, "exit": 2, "error": rejected.stderr})
    cases = [
        {"label": label, "forced": amount, "seed": 2026104901 + i, "seconds": 10}
        for i, (label, amount) in enumerate(itertools.product(("A", "B"), (8, 16, 32)))
    ]
    metadata = {
        "version": "v1.0.0",
        "date": "2026-10-04",
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "sources": {str(p.relative_to(ROOT)): sha(p) for p in snapshots},
        "artifacts": {
            str(p.relative_to(ROOT)): sha(p) for p in sorted(RAW.rglob("*")) if p.is_file()
        },
        "cases": cases,
        "controls": controls,
        "rejected_inputs": rejected_inputs,
        "compiler": compiler,
        "platform": platform.platform(),
        "optimization_runs": 0,
        "scope": "Secondary exploratory diversity test. Temporary outside-elite/protection phase; "
        "then unrestricted fixed64 tabu repair. No global exclusion or lower bound.",
    }
    dump(HERE / "metadata.json", metadata)
    print(
        json.dumps(
            {
                "prepared": True,
                "native_optimization_runs": 0,
                "delta_controls": 1024,
                "metadata_sha256": sha(HERE / "metadata.json"),
            }
        )
    )


def replay_forced(events, initial, elite, forced):
    ids = [IDS[block] for block in initial]
    locked = set()
    rows = [event for event in events if event["event"] == "forced_move"]
    assert len(rows) == forced
    for step, row in enumerate(rows, 1):
        assert row["step"] == step and row["old"] == ids[row["slot"]]
        assert row["old"] not in locked and row["incoming"] not in ids
        assert UNIVERSE[row["incoming"]] not in elite
        before = len(missing([UNIVERSE[i] for i in ids]))
        ids[row["slot"]] = row["incoming"]
        locked.add(row["incoming"])
        after = len(missing([UNIVERSE[i] for i in ids]))
        assert row["ids"] == ids and locked <= set(ids)
        assert (row["before"], row["after"], row["delta"]) == (before, after, after - before)
    assert len(locked) == forced
    return set(ids)


def run():
    metadata = json.loads((HERE / "metadata.json").read_text())
    assert not (HERE / "summary.json").exists()
    for collection in (metadata["sources"], metadata["artifacts"]):
        for relative, expected in collection.items():
            assert sha(ROOT / relative) == expected
    inputs = RAW / "inputs"
    elite = set(read_blocks(inputs / "elite66.txt"))
    results = []
    for case in metadata["cases"]:
        name = f"{case['label']}-f{case['forced']}-s{case['seed']}"
        directory = RAW / name
        directory.mkdir()
        prefix = directory / "search"
        start_path = inputs / f"{case['label']}.txt"
        initial = list(read_blocks(start_path))
        command = [
            str(inputs / "novelty"),
            "run",
            str(start_path),
            str(inputs / "elite66.txt"),
            str(case["forced"]),
            str(case["seed"]),
            "10",
            str(prefix),
        ]
        started = datetime.now(timezone.utc).isoformat()
        process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=25)
        (directory / "stdout.jsonl").write_text(process.stdout)
        (directory / "stderr.txt").write_text(process.stderr)
        assert process.returncode == 0 and not process.stderr, process.stderr
        events = [json.loads(line) for line in process.stdout.splitlines()]
        assert events[0] == {
            "event": "start",
            "seed": case["seed"],
            "seconds": 10,
            "forced": case["forced"],
            "initial_holes": 3,
        }
        forced_ids = replay_forced(events, initial, elite, case["forced"])
        records = []
        for event in events:
            if event["event"] != "saved":
                continue
            path = Path(str(prefix) + "-" + event["label"] + ".txt")
            checked = verify(path)
            family = set(read_blocks(path))
            assert checked["holes"] == event["holes"]
            assert len(family - elite) == event["outside_elite"]
            if event["label"] == "forced":
                assert {IDS[block] for block in family} == forced_ids and len(
                    family - elite
                ) == case["forced"]
            checked.update(
                label=event["label"],
                outside_elite=len(family - elite),
                distance_from_initial=len(family - set(initial)),
            )
            records.append(checked)
        assert {p.name for p in directory.glob("*.txt") if p.name != "stderr.txt"} == {
            Path(row["path"]).name for row in records
        }
        finished = events[-1]
        assert finished["event"] == "finished" and not finished["interrupted"]
        assert finished["seed"] == case["seed"] and finished["forced"] == case["forced"]
        assert finished["overall_best"] == min(record["holes"] for record in records)
        result = {
            **case,
            "started_utc": started,
            "finished_utc": datetime.now(timezone.utc).isoformat(),
            "argv": command,
            "native": finished,
            "saved": records,
            "forced_trace_freshly_replayed": True,
            "artifact_sha256": {p.name: sha(p) for p in sorted(directory.iterdir()) if p.is_file()},
        }
        dump(HERE / f"{name}.json", result)
        results.append(result)
        print(
            json.dumps(
                {
                    "case": name,
                    "forced_holes": next(r["holes"] for r in records if r["label"] == "forced"),
                    "best": finished["overall_best"],
                    "repair_best": finished["repair_best"],
                    "final": finished["final_holes"],
                    "seconds": finished["seconds"],
                    "saved_states": len(records),
                }
            ),
            flush=True,
        )
        if finished["overall_best"] == 0:
            break
    dump(
        HERE / "summary.json",
        {
            "scope": metadata["scope"],
            "metadata_sha256": sha(HERE / "metadata.json"),
            "cases": results,
            "global_lower_bound_claim": False,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "run"))
    args = parser.parse_args()
    (prepare if args.action == "prepare" else run)()
