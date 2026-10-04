# Document:    Gated Weak Pair Two Swap Scan Recorder
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      8c0719bc04bd5da81060b0200c6f9c0770a708cfeb6d8f6d0f77efe492bee91d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""One root-owned bounded enumeration; no automatic retry or optimization loop."""

import argparse
import hashlib
import importlib.util
import itertools
import json
import math
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from covering64.core import verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/weak-pair-two-swap-scan-v2-20261004"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
PAIRS = list(itertools.combinations(range(1, 17), 2))
RANK = {b: i for i, b in enumerate(BLOCKS)}
TOTAL = 18_668_272_896
OUTERS = 8_676_864
INNER = 9_260_056
BUDGET = {
    "passes": 1,
    "seconds": 120,
    "watchdog_seconds": 135,
    "termination_grace_seconds": 5,
    "seed": None,
    "relaunch": False,
    "enumerate_complete_ties": True,
    "budget_reallocation": False,
}
SPEC = importlib.util.spec_from_file_location(
    "standalone_cover_checker", ROOT / "scripts/check_cover.py"
)
STANDALONE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STANDALONE)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def family_text(ids):
    return "".join(" ".join(map(str, BLOCKS[i])) + "\n" for i in sorted(ids))


def inspect_family(ids, cores):
    assert len(ids) == len(set(ids)) == 64 and all(type(i) is int and 0 <= i < 4368 for i in ids)
    blocks = [BLOCKS[i] for i in sorted(ids)]
    counts = {
        n: Counter(q for b in blocks for q in itertools.combinations(b, n)) for n in (2, 3, 4)
    }
    d2max = d2sum = d3 = d4 = 0
    for p in PAIRS:
        pair_count = counts[2][p]
        positions = [(a, counts[3][tuple(sorted((*p, a)))]) for a in range(1, 17) if a not in p]
        vals = sorted((c for _, c in positions), reverse=True)
        maximum = max(0, 12 - 3 * pair_count + vals[0] + vals[1])
        expanded = [
            max(0, 12 - 3 * pair_count + a + b)
            for (_, a), (_, b) in itertools.combinations(positions, 2)
        ]
        assert maximum == max(expanded)
        d2max += maximum
        d2sum += sum(expanded)
        d3 += sum(max(0, 13 - 3 * pair_count + c) for _, c in positions)
        d4 += sum(
            max(0, 12 - 3 * pair_count + 2 * counts[4][tuple(sorted((*p, a, b)))])
            for (a, _), (b, _) in itertools.combinations(positions, 2)
        )
    holes = 560 - len(counts[3])
    metrics = {
        "cardinality": 64,
        "holes": holes,
        "D2max": d2max,
        "D2sum": d2sum,
        "D3": d3,
        "D4": d4,
        "minimum_pair_count": min(counts[2][p] for p in PAIRS),
        "core_overlaps": [len(set(ids) & set(core)) for core in cores],
    }
    package = verify_cover(blocks)
    text = family_text(ids)
    standalone = STANDALONE.verify_cover(STANDALONE.parse_witness(text), expected_blocks=64)
    assert len(package["uncovered"]) == standalone["uncovered_count"] == holes
    assert package["valid"] == standalone["valid"] == (holes == 0)
    assert standalone["cardinality_matches"] and standalone["blocks"] == 64
    return {
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "metrics": metrics,
        "package_valid": package["valid"],
        "standalone_valid": standalone["valid"],
        "canonical_sha256": standalone["canonical_sha256"],
    }


def legal(m):
    return (
        m["cardinality"] == 64
        and m["minimum_pair_count"] >= 5
        and m["D3"] == m["D4"] == 0
        and max(m["core_overlaps"]) <= 55
    )


def shell_started(outer_count):
    q, r = divmod(outer_count, 4304)
    return q * INNER + r * (8607 - r) // 2


def exchange_position(original, outgoing, incoming):
    assert type(outgoing) is list and type(incoming) is list
    assert len(outgoing) == len(incoming) == 2
    assert all(type(v) is int and 0 <= v < 4368 for v in outgoing + incoming)
    b, c = outgoing
    a, d = incoming
    assert b < c and a < d
    assert b in original and c in original and a not in original and d not in original
    outs = sorted(original)
    ins = [i for i in range(4368) if i not in original]
    bi, ci, ai, di = outs.index(b), outs.index(c), ins.index(a), ins.index(d)
    pair_index = bi * (127 - bi) // 2 + ci - bi - 1
    ordinal = pair_index * INNER + ai * (8607 - ai) // 2 + di - ai
    return ordinal, pair_index * 4304 + ai + 1


def validate(prefix, stdout, rc, stderr, elapsed, initial, cores, control_limit=None):
    events = [json.loads(line) for line in stdout.splitlines()]
    assert len(events) >= 2
    assert events[0] == {
        "event": "start",
        "budget_seconds": 120,
        "total": TOTAL,
        "outer_total": OUTERS,
        "control_limit": control_limit,
        "baseline": initial["metrics"],
    }
    final = events[-1]
    assert final["event"] == "final" and final["total"] == TOTAL and final["outer_total"] == OUTERS
    assert type(final["complete"]) is bool
    for name in [
        "total",
        "outer_total",
        "outer_started",
        "outer_completed",
        "evaluated",
        "pair_floor_pruned",
        "eligible_generated",
        "pending_eligible",
        "accounted",
        "last_evaluated_ordinal",
        "legal",
        "strictly_improving_neighbors",
        "strict_improvement_records",
        "best_ties",
    ]:
        assert type(final[name]) is int and final[name] >= 0
    assert type(final["seconds"]) in (int, float) and math.isfinite(final["seconds"])
    assert 0 <= final["seconds"] <= elapsed + 1
    assert len(final["best_rank"]) == 2
    assert all(type(v) is int and v >= 0 for v in final["best_rank"])
    assert not stderr and rc in (0, 1)
    assert final["complete"] == (final["outer_completed"] == OUTERS) == (rc == 0)
    assert 0 <= final["outer_completed"] <= final["outer_started"] <= OUTERS
    assert final["outer_started"] - final["outer_completed"] in (0, 1)
    assert final["accounted"] == final["pair_floor_pruned"] + final["evaluated"] <= TOTAL
    assert final["eligible_generated"] == final["evaluated"] + final["pending_eligible"]
    assert final["pair_floor_pruned"] + final["eligible_generated"] == shell_started(
        final["outer_started"]
    )
    assert final["pending_eligible"] <= 4303
    outer_gap = final["outer_started"] - final["outer_completed"]
    assert (outer_gap == 1) == (final["pending_eligible"] > 0)
    if outer_gap:
        active_tail = 4303 - ((final["outer_started"] - 1) % 4304)
        assert final["pending_eligible"] <= active_tail
    assert 0 <= final["legal"] <= final["evaluated"] <= TOTAL
    assert final["strictly_improving_neighbors"] <= final["legal"]
    assert 0 <= final["last_evaluated_ordinal"] <= shell_started(final["outer_started"])
    assert bool(final["last_evaluated_ordinal"]) == bool(final["evaluated"])
    for name in ("support_bins", "support_shell_bins"):
        assert len(final[name]) == 8 and all(type(v) is int and v >= 0 for v in final[name])
    assert final["support_bins"][3] == final["support_shell_bins"][3] == 0
    assert all(
        shell <= 4303 * outers
        for shell, outers in zip(final["support_shell_bins"], final["support_bins"], strict=True)
    )
    assert sum(final["support_bins"]) == final["outer_started"]
    assert sum(final["support_shell_bins"]) == shell_started(final["outer_started"])
    assert sum(final["support_shell_bins"][:2]) <= final["pair_floor_pruned"]
    if final["complete"]:
        assert final["accounted"] == TOTAL and final["pending_eligible"] == 0
    assert final["reason"] in ("complete", "time_limit", "interrupted", "control_limit")
    assert (final["reason"] == "complete") == final["complete"]
    if final["reason"] == "time_limit":
        assert final["seconds"] >= 120
    if control_limit is not None:
        assert final["reason"] == "control_limit"
        assert final["outer_started"] == final["outer_completed"] == control_limit
    else:
        assert final["reason"] != "control_limit"
    records = events[1:-1]
    assert all(e["event"] == "improvement" for e in records)
    assert (
        len(records) == final["strict_improvement_records"] <= final["strictly_improving_neighbors"]
    )
    assert all(type(r["serial"]) is int and type(r["evaluated"]) is int for r in records)
    assert all(
        type(r["seconds"]) in (int, float) and 0 <= r["seconds"] <= final["seconds"]
        for r in records
    )
    assert all(1 <= r["evaluated"] <= final["evaluated"] for r in records)
    assert all(
        a["evaluated"] < b["evaluated"]
        and a["shell_ordinal"] < b["shell_ordinal"]
        and a["seconds"] <= b["seconds"]
        for a, b in zip(records, records[1:])
    )
    assert [r["serial"] for r in records] == list(range(1, len(records) + 1))
    ties = json.loads(Path(str(prefix) + "-ties.json").read_text())
    assert len(ties) == final["best_ties"] <= final["strictly_improving_neighbors"]
    baseline_rank = (initial["metrics"]["holes"], initial["metrics"]["D2max"])
    best_rank = tuple(final["best_rank"])
    assert bool(ties) == (best_rank < baseline_rank)
    original = set(initial["ids"])
    audited = {}
    for row in records + ties:
        outgoing, incoming = row["outgoing"], row["incoming"]
        ordinal, outer = exchange_position(original, outgoing, incoming)
        assert type(row["shell_ordinal"]) is int and row["shell_ordinal"] == ordinal
        assert ordinal <= final["last_evaluated_ordinal"] and outer <= final["outer_started"]
        key = tuple(outgoing + incoming)
        if key not in audited:
            actual = inspect_family((original - set(outgoing)) | set(incoming), cores)
            assert actual["metrics"] == row["metrics"] and legal(actual["metrics"])
            actual.update({"outgoing": outgoing, "incoming": incoming, "shell_ordinal": ordinal})
            audited[key] = actual
        else:
            assert audited[key]["metrics"] == row["metrics"]
        if "evaluated" in row:
            assert type(row["outer_index"]) is int and row["outer_index"] == outer
    previous = baseline_rank
    for row in records:
        rank = (row["metrics"]["holes"], row["metrics"]["D2max"])
        assert rank < previous
        previous = rank
    assert previous == best_rank
    tie_keys = [tuple(row["outgoing"] + row["incoming"]) for row in ties]
    assert tie_keys == sorted(set(tie_keys))
    for row in ties:
        assert (row["metrics"]["holes"], row["metrics"]["D2max"]) == best_rank < baseline_rank
    return {
        "passed": True,
        "final": final,
        "strict_improvements": records,
        "best_ties": [audited[key] for key in tie_keys],
        "audited_families": list(audited.values()),
    }


def main(gate_path):
    manifest_path = HERE / "manifest.json"
    manifest, gate = json.loads(manifest_path.read_text()), json.loads(gate_path.read_text())
    assert gate["passed"] and gate["manifest_sha256"] == sha(manifest_path)
    assert manifest["budget"] == BUDGET
    for relative, digest in (
        manifest["source_files"] | manifest["input_files"] | manifest["raw_files"]
    ).items():
        assert sha(ROOT / relative) == digest, relative
    assert not (RAW / "start.json").exists() and not (HERE / "result.json").exists()
    binary = ROOT / manifest["binary_path"]
    assert sha(binary) == manifest["binary_sha256"]
    archive = RAW / "frozen-sources"
    archive.mkdir()
    for relative in manifest["source_files"]:
        source = ROOT / relative
        shutil.copyfile(source, archive / source.name)
    shutil.copyfile(manifest_path, archive / "manifest.json")
    shutil.copyfile(gate_path, archive / "gate.json")
    dump(
        RAW / "start.json",
        {
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "manifest_sha256": sha(manifest_path),
            "gate_sha256": sha(gate_path),
            "budget": BUDGET,
        },
    )
    prefix = RAW / "scan"
    command = [str(binary), str(ROOT / manifest["initial"]["path"]), "120", str(prefix)]
    started = time.monotonic()
    process = subprocess.Popen(
        command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    watchdog = {"fired": False, "terminate_sent": False, "kill_sent": False, "relaunch": False}
    try:
        stdout, stderr = process.communicate(timeout=135)
    except subprocess.TimeoutExpired:
        watchdog["fired"] = watchdog["terminate_sent"] = True
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            watchdog["kill_sent"] = True
            process.kill()
            stdout, stderr = process.communicate()
    elapsed = time.monotonic() - started
    (RAW / "stdout.jsonl").write_text(stdout)
    (RAW / "stderr.txt").write_text(stderr)
    result = {
        "manifest_sha256": sha(manifest_path),
        "gate_sha256": sha(gate_path),
        "command": command,
        "returncode": process.returncode,
        "elapsed_seconds": elapsed,
        "watchdog": watchdog,
        "passes": 1,
        "seed": None,
        "budget": BUDGET,
        "scope": "Only the pinned family's two-block-swap neighborhood under named necessary rows.",
    }
    try:
        audit = validate(
            prefix,
            stdout,
            process.returncode,
            stderr,
            elapsed,
            manifest["initial"],
            manifest["core_rows"],
        )
        dump(RAW / "candidate-audit.json", audit)
        result.update(
            {
                "validation_passed": True,
                "final": audit["final"],
                "candidate_audit_path": str((RAW / "candidate-audit.json").relative_to(ROOT)),
                "candidate_audit_sha256": sha(RAW / "candidate-audit.json"),
                "complete_best_tie_hashes": [r["sha256"] for r in audit["best_ties"]],
                "cover_found": any(r["metrics"]["holes"] == 0 for r in audit["best_ties"]),
            }
        )
        if audit["best_ties"]:
            first = audit["best_ties"][0]
            ids = (set(manifest["initial"]["ids"]) - set(first["outgoing"])) | set(
                first["incoming"]
            )
            witness = HERE / "best-representative.txt"
            witness.write_text(family_text(ids))
            assert sha(witness) == first["sha256"]
            result["best_representative_path"] = str(witness.relative_to(ROOT))
            result["best_representative_sha256"] = sha(witness)
            cli = subprocess.run(
                [sys.executable, "scripts/check_cover.py", str(witness), "--expected-blocks", "64"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            assert cli.returncode == int(first["metrics"]["holes"] != 0) and not cli.stderr
            receipt = json.loads(cli.stdout)
            assert receipt["canonical_sha256"] == first["canonical_sha256"]
            (RAW / "representative-standalone.json").write_text(cli.stdout)
            result["representative_standalone_cli_passed"] = True
    except Exception as error:
        result["validation_passed"] = False
        result["validation_error"] = f"{type(error).__name__}: {error}"
    result["raw_files"] = {str(p.relative_to(ROOT)): sha(p) for p in RAW.glob("*") if p.is_file()}
    dump(HERE / "result.json", result)
    assert result["validation_passed"], result.get("validation_error")
    print(
        json.dumps(
            {
                "complete": result["final"]["complete"],
                "evaluated": result["final"]["evaluated"],
                "legal": result["final"]["legal"],
                "best_rank": result["final"]["best_rank"],
                "best_ties": result["final"]["best_ties"],
                "cover_found": result["cover_found"],
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", required=True, type=Path)
    main(parser.parse_args().gate.resolve())
