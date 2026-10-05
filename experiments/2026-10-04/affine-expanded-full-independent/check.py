# Document:    Independent Gate for Full New-Only Affine Support
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      1713dcb7806b1f15026ff0afb6c18fa42d4db58465e13abc1b449f6c1c29fcf3
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Audit mapping and mocked lifecycle; never call the real support screen or solver."""

from __future__ import annotations

import contextlib
import copy
import gzip
import importlib.util
import io
import json
import os
import struct
import subprocess
import tempfile
import time
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "affine-expanded-full-support-v1.0.1"
CATALOG = HERE.parent / "affine-expanded-catalog"
AUDIT_SHA = "66f1cf20c56a7099979ac1184862e9ac1db8f50f1646704121cdd314b00ab5bc"
CORE_SHA = "5007aa2b9b38d980ecb4283aeb23c0873d770ee1e9036d3af0bab1045887428d"
CONTROLS = []


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def rejected(name, operation):
    try:
        operation()
    except (AssertionError, ValueError, EOFError, OSError, KeyError, IndexError):
        CONTROLS.append(name)
    else:
        raise AssertionError(f"Damaged control accepted: {name}")


def inspect_inputs(producer, manifest):
    assert manifest["cooperative_seconds"] == 650
    assert manifest["stop_new_case_seconds"] == 649
    assert manifest["external_watchdog_seconds"] == 660
    assert manifest["termination_grace_seconds"] == 5
    assert manifest["automatic_retry"] is manifest["automatic_resume"] is False
    for path, expected in manifest["input_hashes"].items():
        assert sha(ROOT / path) == expected
    assert sha(HERE.parent / "affine-expanded-independent/audit.json") == AUDIT_SHA
    assert sha(producer.CORE) == CORE_SHA
    context = producer.load_frozen(manifest, time.monotonic())
    # Only loader, locator, and partial-mask preparation are called, never screen().
    core = context["core"]
    original = module(producer.CORE, "independent_original_support_core")
    assert original.TOTAL == 195296 and core.TOTAL == 6739200
    for name in ("screen", "locate", "global_ids"):
        left, right = getattr(core, name).__code__, getattr(original, name).__code__
        assert left.co_code == right.co_code and left.co_consts == right.co_consts
    blocks = list(combinations(range(1, 17), 5))
    triples = list(combinations(range(2, 17), 3))
    assert list(core.BLOCKS) == blocks
    assert list(core.AVOIDING) == blocks[1365:]
    assert list(core.TRIPLES) == triples and len(triples) == 455
    block_sets = [set(block) for block in blocks[1365:]]
    for row, triple in enumerate(triples):
        supports = [i for i, b in enumerate(block_sets) if set(triple) <= b]
        assert len(supports) == 66
        assert sum(1 << i for i in supports) == context["data"]["row_masks"][row]
    profiles = json.loads((HERE.parent / "circulant-chosen-link-catalog/profiles.json").read_text())
    for profile in profiles:
        actual = {tuple(t) for t in profile["excess_triples"] if 1 not in t}
        expected = sum(1 << i for i, t in enumerate(triples) if t in actual)
        assert expected == context["data"]["profile_masks"][profile["profile_id"]]
    old_ids = set(json.loads((CATALOG / "old-to-new-ids.json").read_text()))
    fibers = json.loads((CATALOG / "link-fibers.json").read_text())
    next_index = full_count = old_count = 0
    order_hash = sha256()
    partial_samples = set()
    for fiber in fibers:
        fiber_id = fiber["excess_link_id"]
        start, end = fiber["partial_id_range_half_open"]
        assert start == 5184 * fiber_id and end == start + 5184
        new_ids = [p for p in range(start, end) if p not in old_ids]
        assert new_ids == context["new_partials"][fiber_id]
        partial_samples.update([new_ids[0], new_ids[-1], new_ids[len(new_ids) // 2]])
        for partial_id in range(start, end):
            for profile_id in fiber["profile_ids"]:
                if partial_id in old_ids:
                    old_count += 1
                else:
                    expected = (fiber_id, partial_id, profile_id, full_count)
                    assert producer.locate_new(context, next_index) == expected
                    order_hash.update(struct.pack("<IIII", *expected))
                    next_index += 1
                full_count += 1
    assert (full_count, old_count, next_index) == (6739200, 195296, 6543904)
    assert producer.next_cursor(context, next_index) == {
        "next_new_pair_index": 6543904,
        "next_full_pair_ordinal": None,
    }
    for bad in (-1, 6543904, 1.5, True):
        rejected(f"invalid-new-index-{bad}", lambda bad=bad: producer.locate_new(context, bad))
    for partial_id in sorted(partial_samples):
        ids = struct.unpack_from("<20H", context["payload"], partial_id * 40)
        expected_triples = {t for i in ids for t in combinations(blocks[i][1:], 3)}
        assert len(expected_triples) == 80
        expected_rows = [i for i, t in enumerate(triples) if t in expected_triples]
        producer.prepare_partial(context, partial_id)
        assert context["data"]["partial_indices"] == {partial_id: expected_rows}
        assert context["data"]["partial_masks"] == {
            partial_id: sum(1 << i for i in expected_rows),
        }
    return {
        "full_pair_count": full_count,
        "old_pairs_skipped": old_count,
        "new_pair_count": next_index,
        "ordered_new_identities_sha256": order_hash.hexdigest(),
        "row_carriers_checked": 455,
        "domain_columns_checked": 3003,
        "profile_masks_checked": 1300,
        "partial_masks_checked": len(partial_samples),
        "unchanged_core_functions": ["screen", "locate", "global_ids"],
    }


def synthetic_context():
    return {
        "new_partials": [[0, 1, 2]],
        "new_boundaries": [0, 6],
        "data": {
            "fibers": [{"profile_ids": [0, 1], "partial_id_range_half_open": [0, 3]}],
            "boundaries": [0, 6],
        },
    }


def synthetic_row(index):
    return {
        "new_pair_index": index,
        "pair_ordinal": index,
        "partial_id": index // 2,
        "profile_id": index % 2,
        "excess_link_id": 0,
        "outcome": "survives_single_pass" if index % 2 else "insufficient_support",
        "operation_counts": {"synthetic_steps": 1},
    }


def verify_prefix(raw, cursor):
    files = {
        "cases": "cases.jsonl.gz",
        "survivors": "survivors.jsonl.gz",
        "ledger": "commits.jsonl",
    }
    prefixes = {}
    for name, filename in files.items():
        data = (raw / filename).read_bytes()
        size = cursor["files"][name]["bytes"]
        assert 0 <= size <= len(data)
        prefixes[name] = data[:size]
        assert sha256(data[:size]).hexdigest() == cursor["files"][name]["sha256"]
    entries = [json.loads(line) for line in prefixes["ledger"].splitlines()]
    assert len(entries) == cursor["committed_batches"]
    next_case = 0
    offsets = {"cases": 0, "survivors": 0}
    outcomes, operations = Counter(), Counter()
    for batch, entry in enumerate(entries):
        assert entry["batch_index"] == batch
        assert entry["new_pair_range_half_open"] == [next_case, next_case + entry["cases"]]
        parsed = {}
        for name in offsets:
            member = entry["members"][name]
            assert member["start_byte"] == offsets[name]
            compressed = prefixes[name][member["start_byte"] : member["end_byte"]]
            assert sha256(compressed).hexdigest() == member["compressed_sha256"]
            payload = gzip.decompress(compressed)
            assert sha256(payload).hexdigest() == member["uncompressed_sha256"]
            parsed[name] = [json.loads(line) for line in payload.splitlines()]
            offsets[name] = member["end_byte"]
        rows = parsed["cases"]
        assert len(rows) == entry["cases"]
        for index, row in enumerate(rows, next_case):
            assert row == synthetic_row(index)
            outcomes[row["outcome"]] += 1
            operations.update(row["operation_counts"])
        assert entry["first_full_pair_ordinal"] == rows[0]["pair_ordinal"]
        assert entry["last_full_pair_ordinal"] == rows[-1]["pair_ordinal"]
        expected_survivors = [r for r in rows if r["outcome"] == "survives_single_pass"]
        assert parsed["survivors"] == expected_survivors
        assert entry["survivors"] == len(expected_survivors)
        next_case += len(rows)
    assert offsets == {name: len(prefixes[name]) for name in offsets}
    assert cursor["committed_cases"] == cursor["next_new_pair_index"] == next_case
    assert cursor["next_full_pair_ordinal"] == (None if next_case == 6 else next_case)
    assert dict(outcomes) == cursor["outcomes"] and dict(operations) == cursor["operation_counts"]
    if entries:
        last_line = prefixes["ledger"].splitlines(keepends=True)[-1]
        assert sha256(last_line).hexdigest() == cursor["last_commit_sha256"]
    return next_case


def writer_controls(producer):
    with tempfile.TemporaryDirectory(prefix="affine-gate-writer-") as folder:
        root = Path(folder)
        for mode in (
            "normal",
            "cases-write",
            "survivors-write",
            "ledger-write",
            "before-cursor-replace",
            "after-cursor-replace",
        ):
            raw = root / mode
            with patch.object(producer, "NEW_TOTAL", 6):
                writer = producer.CommittedWriter(
                    raw, "synthetic-manifest", "synthetic-source", synthetic_context()
                )
                initial = json.loads((raw / "cursor.json").read_text())
                assert verify_prefix(raw, initial) == 0
                rows = [synthetic_row(0), synthetic_row(1)]
                outcomes = Counter(row["outcome"] for row in rows)
                operations = Counter({"synthetic_steps": 2})
                if mode == "normal":
                    writer.commit(rows, outcomes, operations)
                    cursor = json.loads((raw / "cursor.json").read_text())
                    assert verify_prefix(raw, cursor) == 2
                    for filename in ("cases.jsonl.gz", "survivors.jsonl.gz", "commits.jsonl"):
                        with (raw / filename).open("ab") as handle:
                            handle.write(b"uncommitted damaged tail")
                    assert verify_prefix(raw, cursor) == 2
                    CONTROLS.append("uncommitted tails ignored at exact cursor offsets")
                    for field in (
                        "committed_cases",
                        "next_new_pair_index",
                        "next_full_pair_ordinal",
                    ):
                        damaged = copy.deepcopy(cursor)
                        damaged[field] += 1
                        rejected(f"damaged-cursor-{field}", lambda d=damaged: verify_prefix(raw, d))
                    for name in ("cases", "survivors", "ledger"):
                        damaged = copy.deepcopy(cursor)
                        damaged["files"][name]["sha256"] = "0" * 64
                        rejected(
                            f"damaged-{name}-prefix-hash", lambda d=damaged: verify_prefix(raw, d)
                        )
                    for damaged in ([], [synthetic_row(1)], [synthetic_row(2), synthetic_row(4)]):
                        rejected(
                            "invalid batch index/order/empty",
                            lambda d=damaged: writer.commit(d, outcomes, operations),
                        )
                    rejected(
                        "no writer resume",
                        lambda: producer.CommittedWriter(raw, "x", "y", synthetic_context()),
                    )
                elif mode.endswith("write"):
                    stream = getattr(writer, mode.split("-")[0])
                    original = stream.write

                    def fail_write(data):
                        original(data[: max(1, len(data) // 2)])
                        stream.flush()
                        raise OSError("synthetic interrupted write")

                    with patch.object(stream, "write", side_effect=fail_write):
                        rejected(mode, lambda: writer.commit(rows, outcomes, operations))
                    assert json.loads((raw / "cursor.json").read_text()) == initial
                    assert verify_prefix(raw, initial) == 0
                else:
                    actual_atomic = producer.atomic_json

                    def fail_atomic(path, value):
                        if mode == "after-cursor-replace":
                            actual_atomic(path, value)
                        raise OSError("synthetic cursor transition interruption")

                    with patch.object(producer, "atomic_json", side_effect=fail_atomic):
                        rejected(mode, lambda: writer.commit(rows, outcomes, operations))
                    committed = json.loads((raw / "cursor.json").read_text())
                    assert verify_prefix(raw, committed) == (2 if mode.startswith("after") else 0)
                writer.close()


def launch_controls(launcher, pins):
    cases = [
        ("success", [0], [], False, False),
        ("nonzero", [2], [], False, False),
        ("term", [subprocess.TimeoutExpired("mock", 660), -15], [None], True, False),
        (
            "kill",
            [subprocess.TimeoutExpired("mock", 660), subprocess.TimeoutExpired("mock", 5), -9],
            [None, None],
            True,
            True,
        ),
        (
            "term-exit-race",
            [subprocess.TimeoutExpired("mock", 660), 0],
            [ProcessLookupError()],
            True,
            False,
        ),
        (
            "kill-exit-race",
            [subprocess.TimeoutExpired("mock", 660), subprocess.TimeoutExpired("mock", 5), 0],
            [None, ProcessLookupError()],
            True,
            True,
        ),
    ]
    with tempfile.TemporaryDirectory(prefix="affine-gate-launch-") as directory:
        root = Path(directory)
        for name, waits, signal_results, timed_out, killed in cases:
            folder = root / name
            folder.mkdir()
            logs, raw, gate = folder / "logs", folder / "raw", folder / "gate.json"
            for filename in ("run.py", "launch.py", "manifest.json"):
                (folder / filename).write_bytes((PRODUCER / filename).read_bytes())
            dump(gate, {"decision": "GO", **pins})
            child = Mock(pid=123456, returncode=waits[-1])
            child.wait.side_effect = waits
            with (
                patch.object(launcher, "HERE", folder),
                patch.object(launcher, "ROOT", root),
                patch.object(launcher, "LOGS", logs),
                patch.object(launcher, "RAW", raw),
                patch.object(launcher, "GATE", gate),
                patch.object(launcher.sys, "argv", ["launch.py", "root-authorized-run"]),
                patch.object(launcher.subprocess, "Popen", return_value=child) as spawn,
                patch.object(launcher.os, "killpg", side_effect=signal_results) as signals,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                launcher.main()
                result = json.loads((folder / "launch-result.json").read_text())
                assert result["external_timeout"] is timed_out
                assert result["forced_kill_after_grace"] is killed
                assert result["returncode"] == waits[-1]
                assert spawn.call_count == 1
                assert spawn.call_args.kwargs["start_new_session"] is True
                env = spawn.call_args.kwargs["env"]
                assert float(env["AFFINE_FULL_STARTED_MONOTONIC"]) > 0
                timeouts = [call.kwargs.get("timeout") for call in child.wait.call_args_list]
                assert 0 < timeouts[0] <= 660
                if timed_out:
                    assert timeouts[1] == 5
                assert signals.call_count == len(signal_results)
                rejected(f"no repeat launch after {name}", launcher.main)
            CONTROLS.append(f"mock watchdog {name}")


def run_controls(producer):
    with tempfile.TemporaryDirectory(prefix="affine-gate-run-") as directory:
        base = Path(directory)
        for mode in ("complete", "cooperative-stop", "loading-timeout", "screen-error"):
            folder = base / mode
            folder.mkdir()
            raw, gate = folder / "raw", folder / "gate.json"
            (folder / "manifest.json").write_bytes((PRODUCER / "manifest.json").read_bytes())
            dump(gate, {"synthetic": True})
            context = synthetic_context()
            screen = Mock(side_effect=lambda _data, ordinal: synthetic_row(ordinal))
            if mode == "screen-error":
                screen.side_effect = [
                    synthetic_row(0),
                    synthetic_row(1),
                    synthetic_row(2),
                    ValueError("synthetic screen failure"),
                ]
            context["core"] = SimpleNamespace(screen=screen)
            clock = Mock(return_value=100.0)
            if mode == "cooperative-stop":
                clock.side_effect = [100.0, 100.0, 100.0, 749.0, 749.0]
            loading = Mock(return_value=context)
            if mode == "loading-timeout":
                loading.side_effect = TimeoutError("synthetic bounded loading")
            with (
                patch.object(producer, "HERE", folder),
                patch.object(producer, "RAW", raw),
                patch.object(producer, "GATE", gate),
                patch.object(producer, "NEW_TOTAL", 6),
                patch.object(producer, "BATCH_SIZE", 2),
                patch.object(producer, "TERMINATE_REQUESTED", False),
                patch.object(producer, "check_gate"),
                patch.object(producer, "load_frozen", loading),
                patch.object(producer, "prepare_partial"),
                patch.object(producer.signal, "signal"),
                patch.object(producer.time, "monotonic", clock),
                patch.dict(os.environ, {"AFFINE_FULL_STARTED_MONOTONIC": "100.0"}),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                code = producer.run()
                result = json.loads((folder / "result.json").read_text())
                if mode == "complete":
                    assert code == 0 and result["status"] == "complete"
                    assert result["evaluated_cases"] == 6
                    assert verify_prefix(raw, result["committed_cursor"]) == 6
                elif mode == "cooperative-stop":
                    assert code == 124 and result["status"] == "cooperative_timeout"
                    assert screen.call_count == 1
                    assert verify_prefix(raw, result["committed_cursor"]) == 1
                elif mode == "loading-timeout":
                    assert code == 124 and result["committed_cursor"] is None
                    screen.assert_not_called()
                else:
                    assert code == 1 and result["status"] == "error"
                    assert result["evaluated_cases"] == 3
                    assert result["uncommitted_evaluations"] == 1
                    assert verify_prefix(raw, result["committed_cursor"]) == 2
                clock.side_effect = None
                clock.return_value = 100.0
                rejected(f"no repeated processing after {mode}", producer.run)
            CONTROLS.append(f"synthetic run {mode}")


def gate_and_deadline_controls(producer):
    with tempfile.TemporaryDirectory(prefix="affine-gate-pins-") as directory:
        folder = Path(directory)
        gate = folder / "gate.json"
        for name in ("manifest.json", "launch.py"):
            (folder / name).write_bytes((PRODUCER / name).read_bytes())
        manifest = json.loads((folder / "manifest.json").read_text())
        valid = {
            "decision": "GO",
            "source_sha256": manifest["source_sha256"],
            "launcher_sha256": manifest["launcher_sha256"],
            "manifest_sha256": sha(folder / "manifest.json"),
        }
        with patch.object(producer, "HERE", folder), patch.object(producer, "GATE", gate):
            dump(gate, valid)
            producer.check_gate(manifest)
            for field in valid:
                damaged = dict(valid)
                damaged[field] = "HOLD" if field == "decision" else "0" * 64
                dump(gate, damaged)
                rejected(f"damaged-gate-{field}", lambda: producer.check_gate(manifest))
    with (
        patch.object(producer.time, "monotonic", return_value=748.999),
        patch.object(producer, "TERMINATE_REQUESTED", False),
    ):
        producer.check_time(100.0)
    with (
        patch.object(producer.time, "monotonic", return_value=749.0),
        patch.object(producer, "TERMINATE_REQUESTED", False),
    ):
        rejected("no input loading at649 seconds", lambda: producer.check_time(100.0))
    with (
        patch.object(producer.time, "monotonic", return_value=100.0),
        patch.object(producer, "TERMINATE_REQUESTED", True),
    ):
        rejected("termination stops loading", lambda: producer.check_time(100.0))


def main():
    pins = json.loads((HERE / "producer-pins.json").read_text())
    assert sha(PRODUCER / "run.py") == pins["source_sha256"]
    assert sha(PRODUCER / "launch.py") == pins["launcher_sha256"]
    assert sha(PRODUCER / "manifest.json") == pins["manifest_sha256"]
    producer = module(PRODUCER / "run.py", "reviewed_affine_full_producer")
    launcher = module(PRODUCER / "launch.py", "reviewed_affine_launcher")
    manifest = json.loads((PRODUCER / "manifest.json").read_text())
    mapping = inspect_inputs(producer, manifest)
    writer_controls(producer)
    run_controls(producer)
    launch_controls(launcher, pins)
    gate_and_deadline_controls(producer)
    review = {
        "passed": True,
        **pins,
        "checker_sha256": sha(__file__),
        **mapping,
        "controls_passed": CONTROLS,
        "control_count": len(CONTROLS),
        "real_support_screen_calls": 0,
        "optimizer_calls": 0,
        "real_child_processes": 0,
        "real_signals": 0,
        "scope": "Producer ordering, input mapping, durable prefix and mocked watchdog gate only",
    }
    dump(HERE / "review.json", review)
    dump(HERE / "gate.json", {"decision": "GO", **pins, "review_sha256": sha(HERE / "review.json")})
    print(
        json.dumps(
            {
                "passed": True,
                "controls": len(CONTROLS),
                "review_sha256": sha(HERE / "review.json"),
                "gate_sha256": sha(HERE / "gate.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
