# Document:    Independent Native Three-Core Search Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      f0046926aaa854304617d2c06a4fbf3c4a581ae7fa4aff959ee25545a7c0d06e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Reconstruct memberships and exercise direct transitions; never launch search."""

import argparse
import hashlib
import itertools
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/native-core-cap-independent-20261004"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
TRIPLES = list(itertools.combinations(range(1, 17), 3))
RANK = {block: i for i, block in enumerate(BLOCKS)}
MAPS = [
    list(range(1, 17)),
    [1, 7, 2, 10, 15, 3, 8, 11, 4, 9, 12, 16, 14, 6, 5, 13],
    [16, 15, 12, 5, 11, 8, 4, 7, 3, 6, 1, 2, 10, 14, 13, 9],
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(command, expected=(0,)):
    process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60)
    assert process.returncode in expected, (command, process.returncode, process.stderr)
    return process


def family(path):
    result = []
    for line in Path(path).read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        block = tuple(sorted(map(int, line.split())))
        assert len(block) == len(set(block)) == 5 and block in RANK
        result.append(block)
    assert len(result) == len(set(result))
    return result


def check_family(path, cores):
    blocks = family(path)
    assert len(blocks) == 64
    counts = Counter(triple for block in blocks for triple in itertools.combinations(block, 3))
    holes = [list(triple) for triple in TRIPLES if counts[triple] == 0]
    canonical = "".join(" ".join(map(str, block)) + "\n" for block in sorted(blocks))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    package = json.loads(
        run(
            ["uv", "run", "covering64", "verify", str(path), "--expected-blocks", "64"], (0, 1)
        ).stdout
    )
    standalone = json.loads(
        run(
            ["uv", "run", "python", "scripts/check_cover.py", str(path), "--expected-blocks", "64"],
            (0, 1),
        ).stdout
    )
    for output in [package, standalone]:
        assert output["blocks"] == 64 and output["canonical_sha256"] == digest
        assert output["uncovered"] == holes and output["valid"] == (not holes)
    heavy = [triple for triple in TRIPLES if counts[triple] >= 6]
    forbidden = []
    for partition in itertools.combinations(heavy, 5):
        if len(set().union(*map(set, partition))) == 15:
            if sum(counts[triple] >= 7 for triple in partition) >= 2:
                forbidden.append(partition)
    ids = {RANK[block] for block in blocks}
    return {
        "path": str(Path(path).relative_to(ROOT)),
        "sha256": sha(path),
        "canonical_sha256": digest,
        "holes": len(holes),
        "uncovered": holes,
        "core_overlaps": [len(ids & set(core)) for core in cores],
        "forbidden_partitions": forbidden,
        "package": package,
        "standalone": standalone,
    }


def main(target):
    target = target.resolve()
    manifest_path = target / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    frozen = manifest["input_files"] | manifest["raw_files"]
    for relative, expected in frozen.items():
        assert sha(ROOT / relative) == expected, relative
    assert manifest["optimizer_calls"] == 0
    assert manifest["budget"] == {
        "runs": 2,
        "seconds_per_run": 60,
        "seeds": [2026104201, 2026104202],
        "watchdog_seconds": 75,
        "termination_grace_seconds": 5,
        "simultaneous_processes": 1,
        "relaunch": False,
    }
    original = ROOT / "experiments/2026-10-03/partial-core-holes/core.txt"
    assert sha(original) == "7011e57be2714b1e1a16d4419ecb55a0160e25806f5db5dd786891aa17d0a5db"
    original_blocks = family(original)
    assert len(original_blocks) == 60
    cores = []
    for mapping in MAPS:
        assert sorted(mapping) == list(range(1, 17))
        cores.append(
            sorted(RANK[tuple(sorted(mapping[x - 1] for x in block))] for block in original_blocks)
        )
    assert cores == manifest["core_rows"]
    third_path = ROOT / "experiments/2026-10-04/third-core-independent/audit.json"
    third = json.loads(third_path.read_text())
    assert cores[2] == third["core_global_ids"]
    membership = [sum((1 << c) for c in range(3) if i in cores[c]) for i in range(4368)]
    block_masks = [sum(1 << (p - 1) for p in block) for block in BLOCKS]
    triple_masks = [sum(1 << (p - 1) for p in triple) for triple in TRIPLES]
    binary = ROOT / manifest["binary_path"]
    assert sha(binary) == manifest["binary_sha256"]
    table = json.loads(run([str(binary), "--dump-cores"]).stdout)
    assert table == {
        "cap": 55,
        "block_masks": block_masks,
        "triple_masks": triple_masks,
        "membership": membership,
    }
    source = (target / "search.cpp").read_text()
    baseline = (ROOT / "scripts/heavy_profile_heuristic.cpp").read_text()
    start, end = "bool forbidden_dfs(", "\nusing CoreCounts"
    native_functions = source[source.index(start) : source.index(end)].strip()
    old_functions = baseline[baseline.index(start) : baseline.index("\nint main(")].strip()
    assert native_functions == old_functions
    proposal_start = "        int slot = randint(64)"
    proposal_end = "        if (state.selected[next]) continue;"

    def proposal(text):
        return text[text.index(proposal_start) : text.index(proposal_end) + len(proposal_end)]

    assert proposal(source) == proposal(baseline)
    for text in [
        "step < 1500000",
        "restarts % 3 == 0 || best == 561 ? initial : best_ids",
        "double phase = double(step) / 1500000;",
        "double temperature = 0.06 + (0.7 + 0.1 * (restarts % 4)) * std::pow(1 - phase, 3);",
        "double delta = state.deficit - before + 8.0 * (int(proposed_forbidden) - int(forbidden));",
    ]:
        assert text in source and text in baseline
    rejection_index = source.index("if (!core_caps_pass(proposed_cores))")
    assert source.index("auto proposed_cores =") < rejection_index
    assert rejection_index < source.index("state.move(slot, next)")
    assert "cores = proposed_cores;\n        } else {\n          state.move(slot, old);" in source
    assert source.count('finish_run(prefix, state.ids, best_ids, "cover_found"') == 2
    assert source.count("finish_run(prefix, final_ids, best_ids, stopped ?") == 1
    assert '(event == "cover_found" && (current.deficit != 0 || best.deficit != 0))' in source
    RAW.mkdir(parents=True, exist_ok=True)
    header = "// Independently regenerated lexicographic tables and point-map memberships.\n"
    for name, values in [
        ("EXPECTED_BLOCKS", block_masks),
        ("EXPECTED_TRIPLES", triple_masks),
        ("EXPECTED_MEMBERSHIP", membership),
    ]:
        header += f"constexpr std::array<unsigned,{len(values)}> {name}="
        header += "{" + ",".join(map(str, values)) + "};\n"
    (RAW / "expected.hpp").write_text(header)
    command = [
        "/usr/bin/clang++",
        "-std=c++20",
        "-O1",
        "-g",
        "-fsanitize=address,undefined",
        "-fno-omit-frame-pointer",
        "-Wall",
        "-Wextra",
        "-pedantic",
        "-I",
        str(target),
        "-I",
        str(RAW),
        str(HERE / "control.cpp"),
        "-o",
        str(RAW / "independent-control"),
    ]
    compiled = run(command)
    assert not compiled.stderr
    process = run([str(RAW / "independent-control")])
    assert not process.stderr
    transitions = json.loads(process.stdout)
    assert transitions["passed"] and transitions["optimizer_calls"] == 0
    for label, text in [
        ("build-stdout", compiled.stdout),
        ("build-stderr", compiled.stderr),
        ("control-stdout", process.stdout),
        ("control-stderr", process.stderr),
    ]:
        (RAW / f"{label}.txt").write_text(text)
    hint = check_family(ROOT / manifest["hint_path"], cores)
    assert hint["holes"] == 10 and hint["core_overlaps"] == [1, 8, 55]
    assert not hint["forbidden_partitions"]
    damaged = []
    for relative in manifest["raw_files"]:
        if "/damaged-" in relative:
            bad = run([str(binary), "--profile", str(ROOT / relative)], (2,))
            assert bad.stderr and not bad.stdout
            damaged.append(
                {
                    "path": relative,
                    "sha256": sha(ROOT / relative),
                    "exit_code": bad.returncode,
                    "stderr": bad.stderr,
                }
            )
    assert len(damaged) == 7
    result = {
        "passed": True,
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": sha(manifest_path),
        "source_sha256": sha(target / "search.cpp"),
        "binary_sha256": sha(binary),
        "runner_sha256": sha(target / "run.py"),
        "check_sha256": sha(__file__),
        "control_sha256": sha(HERE / "control.cpp"),
        "optimizer_calls": 0,
        "unchanged_profile_functions": True,
        "unchanged_proposal_temperature_restart_and_penalty": True,
        "native_table_entries_checked": 13104,
        "core_rows": cores,
        "membership_patterns": dict(sorted(Counter(membership).items())),
        "core_intersections": [[len(set(a) & set(b)) for b in cores] for a in cores],
        "direct_sanitized_transition_controls": transitions,
        "hint": hint,
        "damaged_parser_controls": damaged,
        "compile_command": command,
        "final_status_review": {
            "all_three_exit_paths_delegate_to_common_helper": True,
            "runner_checks_both_return_codes_against_final_snapshots": True,
            "positive_cover_status_tested": False,
            "positive_cover_test_limit": "No valid64cover is available; no fake witness used.",
            "first_revision_withheld": "Zero-hole exits omitted final event and counters.",
        },
        "scope": "Exact three-core membership and direct transition controls. "
        "No optimizer, connectivity or nonexistence claim.",
        "raw_files": {
            str(path.relative_to(ROOT)): sha(path) for path in RAW.iterdir() if path.is_file()
        },
    }
    (HERE / "gate.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "gate_sha256": sha(HERE / "gate.json"),
                "transitions": transitions,
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    main(parser.parse_args().target)
