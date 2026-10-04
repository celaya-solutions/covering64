#!/usr/bin/env python3
# Document:    Independent SQS Pool Native Heuristic Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Finite preparation audit only. Never invoke the native run command."""

import copy
import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

from covering64.core import verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIMARY = HERE.parent / "sqs-pool-heuristic"
RAW = ROOT / "experiments/scratch/sqs-pool-heuristic-independent-20261004"
SOURCE_HASH = "bb8b202dea60e8f32bc882fe93ae0ec76c7f8f5d676785c2fd547f7998ac3cf6"
MANIFEST_HASH = "f63904259b1377960533116ddcd296923f9beeec9b5277ef4512c2ac297e1b8f"
ALL_BLOCKS = list(combinations(range(1, 17), 5))
GLOBAL_IDS = {b: i for i, b in enumerate(ALL_BLOCKS)}
TRIPLES = list(combinations(range(1, 17), 3))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def read_blocks(path):
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    assert blocks == sorted(set(blocks))
    assert all(len(b) == 5 and tuple(sorted(set(b))) == b and set(b) <= set(range(1, 17))
               for b in blocks)
    return blocks


def write_blocks(path, blocks):
    path.write_text("".join(" ".join(map(str, block)) + "\n" for block in sorted(blocks)))


def recount(global_ids, allowed):
    assert len(global_ids) == len(set(global_ids)) == 64
    assert all(type(i) is int and i in allowed for i in global_ids)
    counts = Counter(t for i in global_ids for t in combinations(ALL_BLOCKS[i], 3))
    result = [counts[t] for t in TRIPLES]
    return result, result.count(0)


def replay(rows, initial, allowed):
    assert len(rows) == 96
    current, accepted, checkpoints = list(initial), 0, 0
    states = {tuple(sorted(current))}
    for step, row in enumerate(rows):
        assert row["step"] == step
        action = ("accepted", "rejected", "rollback")[step % 3]
        assert row["action"] == action
        before_counts, before_holes = recount(current, allowed)
        slot, added = row["slot"], row["added_global_id"]
        assert type(slot) is int and 0 <= slot < 64
        assert added in allowed and added not in current
        assert row["removed_global_id"] == current[slot]
        tentative = list(current)
        tentative[slot] = added
        tentative_counts, tentative_holes = recount(tentative, allowed)
        delta = tentative_holes - before_holes
        assert row["delta"] == delta and row["holes_before"] == before_holes
        assert row["tentative_holes"] == tentative_holes
        if action == "accepted":
            current = tentative
            accepted += 1
            states.add(tuple(sorted(current)))
        elif action == "rollback":
            assert delta > 0
            states.add(tuple(sorted(tentative)))
        else:
            assert action == "rejected"
        expected_counts = tentative_counts if action == "accepted" else before_counts
        expected_holes = tentative_holes if action == "accepted" else before_holes
        assert row["selected_ids"] == current
        assert row["cached_counts"] == expected_counts
        assert row["holes_after"] == expected_holes
        assert row["accepted_total"] == accepted
        periodic = action == "accepted" and accepted % 4 == 0
        assert row["periodic_audit"] is periodic
        checkpoints += periodic
    assert accepted == 32 and checkpoints == 8
    return states


def verify_states(states, allowed):
    directory = RAW / "states"
    directory.mkdir(exist_ok=True)
    results = []
    for index, ids in enumerate(sorted(states)):
        path = directory / f"state-{index:03d}.txt"
        blocks = [ALL_BLOCKS[i] for i in ids]
        write_blocks(path, blocks)
        counts, holes = recount(ids, allowed)
        package = verify_cover(blocks)
        process = subprocess.run(
            [sys.executable, "-I", str(ROOT / "scripts/check_cover.py"), str(path),
             "--expected-blocks", "64"], capture_output=True, text=True, check=False,
        )
        independent = json.loads(process.stdout)
        assert process.returncode in (0, 1)
        assert package["blocks"] == independent["blocks"] == 64
        assert independent["cardinality_matches"] is True
        assert package["canonical_sha256"] == independent["canonical_sha256"] == sha(path)
        assert len(package["uncovered"]) == independent["uncovered_count"] == holes
        assert set(package["uncovered"]) == set(map(tuple, independent["uncovered"]))
        assert package["valid"] == independent["valid"] == (holes == 0)
        expected_histogram = {int(k): v for k, v
                              in independent["coverage_multiplicities"].items()}
        assert Counter(counts) == Counter(expected_histogram)
        save(path.with_suffix(".package.json"), package)
        save(path.with_suffix(".standalone.json"), independent)
        results.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path), "holes": holes})
    return results


def native_controls(manifest, pool_file, initial_file):
    source = ROOT / manifest["source_path"]
    binary = RAW / "native-asan-ubsan"
    compile_record = RAW / "compile.json"
    command = ["/usr/bin/c++", "-std=c++17", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
               "-fsanitize=address,undefined", "-fno-omit-frame-pointer", str(source),
               "-o", str(binary)]
    if not compile_record.exists():
        process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=60)
        save(compile_record, {"argv": command, "returncode": process.returncode,
                              "stdout": process.stdout, "stderr": process.stderr,
                              "source_sha256": sha(source),
                              "binary_sha256": sha(binary) if binary.exists() else None})
    compiled = json.loads(compile_record.read_text())
    assert compiled["argv"] == command and compiled["returncode"] == 0
    assert compiled["source_sha256"] == SOURCE_HASH and compiled["binary_sha256"] == sha(binary)
    prepared = RAW / "sanitizer-preparation"
    if not prepared.exists():
        process = subprocess.run([str(binary), "prepare", str(pool_file), str(prepared)],
                                 capture_output=True, text=True, check=False, timeout=60)
        save(RAW / "prepare-process.json", {"returncode": process.returncode,
                                            "stdout": process.stdout, "stderr": process.stderr})
    process = json.loads((RAW / "prepare-process.json").read_text())
    assert process["returncode"] == 0 and process["stderr"] == ""
    normal = (ROOT / manifest["initial_path"]).parent
    for name in ("initial64.txt", "greedy-trace.csv", "initial-deltas.csv",
                 "move-controls.jsonl", "preparation.json"):
        assert sha(prepared / name) == sha(normal / name)
    damage_dir = RAW / "malformed"
    damage_dir.mkdir(exist_ok=True)
    initial_lines = initial_file.read_text().splitlines()
    pool_lines = pool_file.read_text().splitlines()
    outside = next(b for b in ALL_BLOCKS if b not in set(read_blocks(pool_file)))
    outside_start = sorted(read_blocks(initial_file)[:-1] + [outside])
    cases = [
        ("start-too-few", "start", initial_lines[:-1]),
        ("start-too-many", "start", initial_lines + [initial_lines[-1]]),
        ("start-duplicate", "start", [initial_lines[0]] + initial_lines[:-1]),
        ("start-out-of-pool", "start", [" ".join(map(str, b)) for b in outside_start]),
        ("start-blank-row", "start", [""] + initial_lines[1:]),
        ("start-junk-token", "start", ["1 2 3 4 5x"] + initial_lines[1:]),
        ("start-float-token", "start", ["1.0 2 3 4 5"] + initial_lines[1:]),
        ("start-overflow-token", "start", ["999999999999999999 2 3 4 5"] + initial_lines[1:]),
        ("start-zero-label", "start", ["0 2 3 4 5"] + initial_lines[1:]),
        ("start-label17", "start", ["1 2 3 4 17"] + initial_lines[1:]),
        ("start-repeat-point", "start", ["1 2 3 4 4"] + initial_lines[1:]),
        ("start-four-points", "start", ["1 2 3 4"] + initial_lines[1:]),
        ("start-six-points", "start", ["1 2 3 4 5 6"] + initial_lines[1:]),
        ("start-reversed-points", "start", ["5 4 3 2 1"] + initial_lines[1:]),
        ("start-unordered-blocks", "start",
         [initial_lines[1], initial_lines[0]] + initial_lines[2:]),
        ("pool-too-few", "pool", pool_lines[:-1]),
        ("pool-too-many", "pool", pool_lines + [pool_lines[-1]]),
        ("pool-duplicate", "pool", [pool_lines[0]] + pool_lines[:-1]),
        ("pool-bad-token", "pool", ["1 2 3 4 5x"] + pool_lines[1:]),
        ("pool-unordered", "pool", [pool_lines[1], pool_lines[0]] + pool_lines[2:]),
    ]
    results = []
    for name, kind, lines in cases:
        path = damage_dir / f"{name}.txt"
        path.write_text("\n".join(lines) + "\n")
        for executable in (ROOT / manifest["binary_path"], binary):
            process = subprocess.run(
                [str(executable), "validate", str(path if kind == "pool" else pool_file),
                 str(path if kind == "start" else initial_file)],
                capture_output=True, text=True, check=False, timeout=10,
            )
            assert process.returncode == 2 and process.stdout == ""
            assert "AddressSanitizer" not in process.stderr
            assert "runtime error:" not in process.stderr
            results.append({"name": name, "binary_sha256": sha(executable),
                            "returncode": process.returncode, "stderr": process.stderr})
    for executable in (ROOT / manifest["binary_path"], binary):
        process = subprocess.run([str(executable), "validate", str(pool_file), str(initial_file)],
                                 capture_output=True, text=True, check=False, timeout=10)
        assert process.returncode == 0 and process.stderr == ""
        assert json.loads(process.stdout) == {"well_formed": True, "blocks": 64, "holes": 31}
    save(RAW / "malformed-controls.json", results)
    return {"sanitizer_binary_sha256": sha(binary), "sanitizer_preparation_matches": True,
            "malformed_cases": len(cases), "malformed_runs_rejected": len(results),
            "sanitizer_stderr": ""}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = PRIMARY / "manifest.json"
    assert sha(manifest_path) == MANIFEST_HASH
    manifest = json.loads(manifest_path.read_text())
    verified = dict(manifest["artifacts"])
    verified[str(manifest_path.relative_to(ROOT))] = MANIFEST_HASH
    for name in ("check.py", "reconstruct.py", "expected.json", "expected-greedy.txt"):
        verified[str((HERE / name).relative_to(ROOT))] = sha(HERE / name)
    assert all(sha(ROOT / p) == value for p, value in verified.items())
    assert manifest["source_sha256"] == SOURCE_HASH
    assert manifest["optimization_runs"] == 0
    spec = importlib.util.spec_from_file_location("independent_recount", HERE / "reconstruct.py")
    reference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reference)
    pool = reference.pool_blocks()
    pool_file, initial_file = ROOT / manifest["pool_path"], ROOT / manifest["initial_path"]
    assert read_blocks(pool_file) == pool
    allowed = {GLOBAL_IDS[b] for b in pool}
    selected, trace = reference.greedy(pool)
    initial = sorted(GLOBAL_IDS[pool[i]] for i in selected)
    assert read_blocks(initial_file) == [ALL_BLOCKS[i] for i in initial]
    assert sha(initial_file) == sha(HERE / "expected-greedy.txt")
    preparation = initial_file.parent
    rows = list(csv.DictReader((preparation / "greedy-trace.csv").open()))
    assert len(rows) == 64
    for row, expected in zip(rows, trace, strict=True):
        assert {k: int(v) for k, v in row.items()} == {
            "step": expected["step"] + 1, "global_id": GLOBAL_IDS[tuple(expected["block"])],
            "gain": expected["gain"], "holes": expected["holes"]}
    expected_deltas = {(GLOBAL_IDS[pool[old]], GLOBAL_IDS[pool[new]]): delta
                       for old, new, delta in reference.initial_deltas(pool, selected)}
    seen, histogram = set(), Counter()
    with (preparation / "initial-deltas.csv").open() as stream:
        for strings in csv.DictReader(stream):
            row = {k: int(v) for k, v in strings.items()}
            old, new, slot = row["removed_global_id"], row["added_global_id"], row["slot"]
            assert 0 <= slot < 64 and initial[slot] == old
            key = (old, new)
            assert key in expected_deltas and key not in seen
            assert row["delta"] == expected_deltas[key]
            assert row["holes_after"] == 31 + expected_deltas[key]
            seen.add(key)
            histogram[row["delta"]] += 1
    assert len(seen) == len(expected_deltas) == 107520
    move_rows = [json.loads(line) for line in (preparation / "move-controls.jsonl").read_text()
                 .splitlines()]
    states = replay(move_rows, initial, allowed)
    damaged = []
    mutations = [
        ("wrong-delta", lambda r: r[0].__setitem__("delta", r[0]["delta"] + 1)),
        ("wrong-holes", lambda r: r[0].__setitem__("holes_after", r[0]["holes_after"] + 1)),
        ("wrong-count", lambda r: r[0]["cached_counts"].__setitem__(0, 999)),
        ("wrong-removed-id", lambda r: r[0].__setitem__("removed_global_id", 999)),
        ("duplicate-state-id", lambda r: r[0]["selected_ids"].__setitem__(
            1, r[0]["selected_ids"][0])),
        ("wrong-accepted-total", lambda r: r[0].__setitem__("accepted_total", 0)),
        ("wrong-checkpoint", lambda r: r[9].__setitem__("periodic_audit", False)),
        ("wrong-tentative-holes", lambda r: r[2].__setitem__("tentative_holes", -1)),
        ("wrong-rollback-state", lambda r: r[2]["selected_ids"].reverse()),
    ]
    for name, mutate in mutations:
        changed = copy.deepcopy(move_rows)
        mutate(changed)
        try:
            replay(changed, initial, allowed)
        except (AssertionError, KeyError, IndexError):
            damaged.append(name)
        else:
            raise AssertionError(f"damaged trace accepted: {name}")
    sanitizer = native_controls(manifest, pool_file, initial_file)
    state_checks = verify_states(states, allowed)
    assert all(sha(ROOT / p) == value for p, value in verified.items())
    for p in sorted(RAW.rglob("*")):
        if p.is_file() and not p.name.endswith(".txt"):
            verified[str(p.relative_to(ROOT))] = sha(p)
    result = {
        "passed": True, "manifest_sha256": MANIFEST_HASH, "source_sha256": sha(Path(__file__)),
        "verified_inputs": verified, "native_source_sha256": SOURCE_HASH,
        "pool_size": 1744, "initial_holes": 31, "greedy_steps_checked": 64,
        "initial_legal_deltas_checked": len(seen),
        "delta_histogram": dict(sorted(histogram.items())),
        "move_proposals_checked": 96, "accepted_moves": 32, "rejected_moves": 32,
        "positive_delta_apply_rollback_moves": 32, "accepted_count_checkpoints": 8,
        "damaged_traces_rejected": damaged, "both_verifiers_state_count": len(state_checks),
        "state_checks": state_checks, "sanitizer": sanitizer, "optimization_runs": 0,
        "source_review": {"all_start_paths_check_pool_membership": True,
                          "greedy_iterates_only_allowed_pool": True,
                          "proposals_use_only_allowed_or_allowed_triple_carriers": True,
                          "delta_and_apply_check_incoming_pool_membership": True,
                          "state_constructor_and_full_audit_check_all_members": True,
                          "degree_or_symmetry_constraints": False,
                          "runner_checks_frozen_pool_and_all_manifest_hashes": True,
                          "runtime_full_recount_every_accepted_moves": 4096},
        "scope": "Finite implementation gate for the frozen1744-pool heuristic. No timed "
                 "optimization, cover, or global lower bound is claimed.",
    }
    save(HERE / "gate.json", result)
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("verified_inputs", "state_checks")}), flush=True)


if __name__ == "__main__":
    main()
