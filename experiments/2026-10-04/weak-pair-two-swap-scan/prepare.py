# Document:    Weak Pair Two Swap Scan Preparation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      775570fb3e64c20619bb9b5b993d2a1e970b1bf8ffbc2dd36557241dd77232f5
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Build and run fixed controls only; full enumeration belongs to root after its gate."""

import copy
import hashlib
import json
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from run import (
    BUDGET,
    HERE,
    OUTERS,
    RANK,
    RAW,
    ROOT,
    STANDALONE,
    TOTAL,
    dump,
    exchange_position,
    inspect_family,
    legal,
    sha,
    shell_started,
    validate,
)

NEW_PATH = "experiments/2026-10-04/weak-pair-swap-scan/best-representative.txt"
OLD_PATH = (
    "experiments/2026-10-04/native-variable-cardinality/seed-2026104702/"
    "search-final-admissible64.txt"
)
NEW_SHA = "44e0ee69fb32f37eed00955e25c699a72430d85871ca03a348c0bf572edb7a0a"
OLD_SHA = "330788e4a6f24e1852b047f5cd2447bfa83da66ea8c6daba3287eb53088c4b00"
REUSED = {
    "scan.hpp": "65d59df903e5da7a646a3764f469905ec6705e958d680d9c98eb17445734d560",
    "kernel.hpp": "d374d813225b03d8ac9085255f9c0548e14a31a611bdc7ec5abeb0cce2040fd3",
    "cores.hpp": "054c89d9fed5fdc8e3b511c6452ae3fb14df4b40e64c993772401a264f30e92d",
}


def freeze_header(path):
    lines = path.read_text().splitlines(keepends=True)
    digest = hashlib.sha256("".join(lines[9:]).encode()).hexdigest()
    lines[5] = re.sub(r"SHA256:      .*", "SHA256:      " + digest, lines[5])
    path.write_text("".join(lines))


def main():
    assert not (HERE / "manifest.json").exists(), "already frozen"
    RAW.mkdir(parents=True, exist_ok=True)
    for name, digest in REUSED.items():
        assert sha(HERE / name) == digest
    for path in HERE.iterdir():
        if path.suffix in (".cpp", ".hpp", ".py") and path.name not in REUSED:
            freeze_header(path)
    origin = HERE.with_name("native-variable-cardinality") / "manifest.json"
    cores = json.loads(origin.read_text())["core_rows"]
    checks = []
    for relative, digest in [(OLD_PATH, OLD_SHA), (NEW_PATH, NEW_SHA)]:
        path = ROOT / relative
        assert sha(path) == digest
        blocks = STANDALONE.parse_witness(path.read_text())
        ids = sorted(RANK[tuple(b)] for b in blocks)
        receipt = inspect_family(ids, cores)
        assert receipt["sha256"] == digest and legal(receipt["metrics"])
        receipt.update({"path": relative, "ids": ids})
        cli = subprocess.run(
            [sys.executable, "scripts/check_cover.py", str(path), "--expected-blocks", "64"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert cli.returncode == 1 and not cli.stderr
        assert json.loads(cli.stdout)["canonical_sha256"] == receipt["canonical_sha256"]
        checks.append(receipt)
    old, initial = checks
    assert len(set(old["ids"]) - set(initial["ids"])) == 2
    assert len(set(initial["ids"]) - set(old["ids"])) == 2
    assert (old["metrics"]["holes"], old["metrics"]["D2max"]) == (12, 34)
    assert (initial["metrics"]["holes"], initial["metrics"]["D2max"]) == (12, 29)
    compiler = Path("/usr/bin/clang++")
    sanitizer = ["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
    builds = []
    for source, name, flags in [
        ("search.cpp", "scan", ["-O3", "-DNDEBUG"]),
        ("control.cpp", "controls", sanitizer),
        ("search.cpp", "zero-control", [*sanitizer, "-DTS_CONTROL_LIMIT=0"]),
    ]:
        command = [
            str(compiler),
            "-std=c++20",
            *flags,
            "-Wall",
            "-Wextra",
            "-pedantic",
            str(HERE / source),
            "-o",
            str(RAW / name),
        ]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        (RAW / f"build-{name}.stdout").write_text(result.stdout)
        (RAW / f"build-{name}.stderr").write_text(result.stderr)
        assert result.returncode == 0 and not result.stderr, result.stderr
        builds.append(
            {"command": command, "returncode": result.returncode, "binary_sha256": sha(RAW / name)}
        )
    command = [str(RAW / "controls"), str(ROOT / OLD_PATH), str(ROOT / NEW_PATH)]
    result = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30
    )
    (RAW / "controls.stdout.json").write_text(result.stdout)
    (RAW / "controls.stderr.txt").write_text(result.stderr)
    assert result.returncode == 0 and not result.stderr, result.stderr
    fixed = json.loads(result.stdout)
    assert fixed["passed"]
    prefix = RAW / "zero-control-output"
    zero_command = [str(RAW / "zero-control"), str(ROOT / NEW_PATH), "120", str(prefix)]
    start = time.monotonic()
    result = subprocess.run(
        zero_command, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30
    )
    elapsed = time.monotonic() - start
    (RAW / "zero.stdout.jsonl").write_text(result.stdout)
    (RAW / "zero.stderr.txt").write_text(result.stderr)
    zero = validate(
        prefix,
        result.stdout,
        result.returncode,
        result.stderr,
        elapsed,
        initial,
        cores,
        control_limit=0,
    )
    assert zero["final"]["evaluated"] == 0 and not zero["final"]["complete"]
    # Synthetic recorder fixture: a real positive witness at its true ordinal.
    # These counters describe a log fixture, never an executed scan prefix.
    outgoing = sorted(set(old["ids"]) - set(initial["ids"]))
    incoming = sorted(set(initial["ids"]) - set(old["ids"]))
    ordinal, outer = exchange_position(set(old["ids"]), outgoing, incoming)
    fixture_prefix = RAW / "synthetic-recorder"
    tie = {
        "outgoing": outgoing,
        "incoming": incoming,
        "shell_ordinal": ordinal,
        "metrics": initial["metrics"],
    }
    dump(Path(str(fixture_prefix) + "-ties.json"), [tie])
    fixture_events = [
        {
            "event": "start",
            "budget_seconds": 120,
            "total": TOTAL,
            "outer_total": OUTERS,
            "control_limit": None,
            "baseline": old["metrics"],
        },
        {
            "event": "improvement",
            "serial": 1,
            "evaluated": 1,
            "outer_index": outer,
            "seconds": 0.05,
            **tie,
        },
        {
            "event": "final",
            "complete": False,
            "reason": "interrupted",
            "total": TOTAL,
            "outer_total": OUTERS,
            "outer_started": outer,
            "outer_completed": outer - 1,
            "evaluated": 1,
            "eligible_generated": 1,
            "pending_eligible": 0,
            "pair_floor_pruned": shell_started(outer) - 1,
            "accounted": shell_started(outer),
            "last_evaluated_ordinal": ordinal,
            "legal": 1,
            "strictly_improving_neighbors": 1,
            "strict_improvement_records": 1,
            "best_ties": 1,
            "best_rank": [12, 29],
            "support_bins": [0, 0, outer, 0, 0, 0, 0, 0],
            "support_shell_bins": [0, 0, shell_started(outer), 0, 0, 0, 0, 0],
            "seconds": 0.1,
        },
    ]

    def encode(events):
        return "".join(json.dumps(event) + "\n" for event in events)

    (RAW / "synthetic-recorder.stdout.jsonl").write_text(encode(fixture_events))
    fixture = validate(fixture_prefix, encode(fixture_events), 1, "", 0.2, old, cores)
    assert fixture["best_ties"][0]["sha256"] == NEW_SHA
    rejected = []
    mutations = [
        ("false_completion_reason", lambda e: e[-1].update(reason="complete")),
        ("bool_complete", lambda e: e[-1].update(complete=0)),
        ("bool_counter", lambda e: e[-1].update(legal=True)),
        ("negative_counter", lambda e: e[-1].update(legal=-1)),
        ("counter_above_total", lambda e: e[-1].update(evaluated=TOTAL + 1)),
        ("negative_time", lambda e: e[-1].update(seconds=-1)),
        ("premature_timeout", lambda e: e[-1].update(reason="time_limit")),
        ("wrong_ordinal", lambda e: e[1].update(shell_ordinal=ordinal - 1)),
        ("wrong_incoming", lambda e: e[1].update(incoming=outgoing)),
    ]
    for name, mutate in mutations:
        damaged = copy.deepcopy(fixture_events)
        mutate(damaged)
        try:
            validate(fixture_prefix, encode(damaged), 1, "", 0.2, old, cores)
        except (AssertionError, KeyError, ValueError):
            rejected.append(name)
        else:
            raise AssertionError(f"damaged recorder fixture accepted: {name}")
    dump(Path(str(fixture_prefix) + "-ties.json"), [tie, tie])
    damaged = copy.deepcopy(fixture_events)
    damaged[-1].update(best_ties=2, strictly_improving_neighbors=2, legal=2)
    try:
        validate(fixture_prefix, encode(damaged), 1, "", 0.2, old, cores)
    except AssertionError:
        rejected.append("duplicate_tie")
    else:
        raise AssertionError("duplicate tie accepted")
    dump(Path(str(fixture_prefix) + "-ties.json"), [tie])
    assert len(rejected) == 10
    dump(
        HERE / "controls.json",
        {
            "passed": True,
            "fixed_command": command,
            "fixed": fixed,
            "zero_command": zero_command,
            "zero": zero,
            "input_checks": checks,
            "sanitizers": ["address", "undefined"],
            "full_enumeration_calls": 0,
            "synthetic_recorder_fixture": fixture,
            "synthetic_fixture_is_not_an_executed_prefix": True,
            "damaged_recorder_fixtures_rejected": rejected,
        },
    )
    sources = [p for p in HERE.iterdir() if p.suffix in (".cpp", ".hpp", ".py")]
    inputs = [
        ROOT / OLD_PATH,
        ROOT / NEW_PATH,
        origin,
        HERE / "controls.json",
        ROOT / "uv.lock",
        ROOT / "scripts/check_cover.py",
        ROOT / "src/covering64/core.py",
        HERE.with_name("weak-pair-swap-scan") / "result.json",
        HERE.with_name("weak-pair-swap-scan-runtime-independent") / "postcheck.json",
    ]
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "budget": BUDGET,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_files": {str(p.relative_to(ROOT)): sha(p) for p in sources},
        "input_files": {str(p.relative_to(ROOT)): sha(p) for p in inputs},
        "raw_files": {str(p.relative_to(ROOT)): sha(p) for p in RAW.rglob("*") if p.is_file()},
        "initial": initial,
        "positive_control": old,
        "core_rows": cores,
        "universe_blocks": 4368,
        "selected_blocks": 64,
        "incoming_blocks": 4304,
        "total_neighbors": TOTAL,
        "outer_states": OUTERS,
        "labels": "1-based",
        "block_ID_order": "global lexicographic",
        "affected_pairs": "union of pairs in all four changed blocks, including intersection pairs",
        "weak_rows": {"pair_floor": 120, "single": 1680, "quad": 10920, "core_caps": 4},
        "restrictions": [
            "exactly64 distinct",
            "pair floor5",
            "all single cuts",
            "all quad cuts",
            "four named core caps55",
        ],
        "not_imposed": ["hard D2zero", "regularity", "symmetry", "global profile", "new core cuts"],
        "rank": ["holes", "sum of per-pair maximum stronger deficits"],
        "reported_separately": "sum of all10920 stronger-row deficits",
        "save_policy": (
            "all final best ties strictly improving baseline; each compact out/in record has "
            "full family hash and two checker receipts; strict-improvement witnesses also checked"
        ),
        "neighborhood_scope_only": True,
        "no_global_infeasibility_conclusion": True,
        "full_enumeration_launched": False,
        "reused_file_hashes": REUSED,
        "binary_path": str((RAW / "scan").relative_to(ROOT)),
        "binary_sha256": sha(RAW / "scan"),
        "compiler_path": str(compiler),
        "compiler_sha256": sha(compiler),
        "compiler_version": subprocess.check_output([str(compiler), "--version"], text=True),
        "builds": builds,
        "python_version": sys.version,
        "platform": platform.platform(),
        "controls_sha256": sha(HERE / "controls.json"),
        "standalone_checker_mode": (
            "direct independent parse_witness+verify_cover for every compact family; "
            "CLI for inputs and representative"
        ),
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "prepared": True,
                "manifest_sha256": sha(HERE / "manifest.json"),
                "controls_sha256": sha(HERE / "controls.json"),
                "full_enumeration_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
