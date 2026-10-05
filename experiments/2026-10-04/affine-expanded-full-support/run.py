# Document:    Gated Full New-Only Affine Support Pass
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      53f8b051c223829870d1fe680d7ff0c3196edf61d784b7cb3b649bddcf16812a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Preparation is allowed; root alone may launch after the independent GO gate."""

import bisect
import gzip
import importlib.util
import json
import os
import signal
import struct
import subprocess
import sys
import time
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
CATALOG = BASE / "affine-expanded-catalog"
OLD = BASE / "circulant-chosen-link-catalog"
CORE = BASE / "circulant-chosen-link-support-screen/run.py"
AUDIT = BASE / "affine-expanded-independent/audit.json"
GATE = BASE / "affine-expanded-full-independent/gate.json"
RAW = ROOT / "experiments/scratch/affine-expanded-full-support-v1.0.0"
TOTAL = 6739200
NEW_TOTAL = 6543904
STOP_NEW_SECONDS = 649.0
COOPERATIVE_SECONDS = 650.0
BATCH_SIZE = 1000
TERMINATE_REQUESTED = False


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def atomic_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("wb") as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def prepare():
    require(not (HERE / "manifest.json").exists() and not RAW.exists(), "fresh preparation")
    catalog = load(CATALOG / "summary.json")
    require(
        sha(AUDIT) == "66f1cf20c56a7099979ac1184862e9ac1db8f50f1646704121cdd314b00ab5bc",
        "root accepted catalog and benchmark audit",
    )
    require(sha(CORE) == load(CORE.parent / "manifest.json")["source_sha256"], "frozen core")
    inputs = {
        CATALOG / "summary.json",
        CATALOG / "link-fibers.json",
        CATALOG / "old-to-new-ids.json",
        ROOT / catalog["catalog_path"],
        OLD / "profiles.json",
        OLD / "partial-catalog.json",
        CORE,
        CORE.parent / "manifest.json",
        AUDIT,
    }
    manifest = {
        "source_sha256": sha(__file__),
        "launcher_sha256": sha(HERE / "launch.py"),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "input_hashes": {str(p.relative_to(ROOT)): sha(p) for p in sorted(inputs)},
        "core_source": str(CORE.relative_to(ROOT)),
        "core_function_unchanged": "screen, locate, global_ids",
        "module_constant_overrides": {"TOTAL": {"before": 195296, "after": TOTAL}},
        "other_module_overrides": [],
        "all_pairs": TOTAL,
        "old_pairs_skipped": 195296,
        "new_pairs": NEW_TOTAL,
        "full_pair_order": catalog["pair_order"],
        "new_pair_order": "same full order with precisely mapped old partial IDs skipped",
        "residual_triple_rows": 455,
        "cardinality_demand": 44,
        "avoiding_point_one_domain": 3003,
        "partial_loading": "one partial mask at a time, reused for all its associated profiles",
        "batch_cases": BATCH_SIZE,
        "cooperative_seconds": COOPERATIVE_SECONDS,
        "stop_new_case_seconds": STOP_NEW_SECONDS,
        "external_watchdog_seconds": 660.0,
        "termination_grace_seconds": 5.0,
        "budget_scope": "launcher validation, source/input loading, processing and all output",
        "cursor_authority": "atomic cursor pins durable gzip-member and ledger prefixes",
        "automatic_retry": False,
        "automatic_resume": False,
        "independent_gate": str(GATE.relative_to(ROOT)),
        "root_launch_required": True,
        "optimizer": False,
        "raw_output": str(RAW.relative_to(ROOT)),
    }
    atomic_json(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "source_sha256": manifest["source_sha256"],
                "launcher_sha256": manifest["launcher_sha256"],
                "manifest_sha256": sha(HERE / "manifest.json"),
            },
            sort_keys=True,
        )
    )


def check_gate(manifest):
    gate = load(GATE)
    require(gate["decision"] == "GO", "independent GO gate")
    require(gate["source_sha256"] == manifest["source_sha256"] == sha(__file__), "runner pin")
    require(
        gate["launcher_sha256"] == manifest["launcher_sha256"] == sha(HERE / "launch.py"),
        "launcher pin",
    )
    require(gate["manifest_sha256"] == sha(HERE / "manifest.json"), "manifest gate pin")


def check_time(started):
    if time.monotonic() - started >= STOP_NEW_SECONDS or TERMINATE_REQUESTED:
        raise TimeoutError("preparation stopped within the shared run budget")


def load_frozen(manifest, started):
    for relative, expected in manifest["input_hashes"].items():
        check_time(started)
        require(sha(ROOT / relative) == expected, "frozen input pin")
    spec = importlib.util.spec_from_file_location("frozen_full_affine_core", CORE)
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    require(core.TOTAL == 195296, "original core TOTAL")
    core.TOTAL = TOTAL
    catalog = load(CATALOG / "summary.json")
    fibers = load(CATALOG / "link-fibers.json")
    old_ids = load(CATALOG / "old-to-new-ids.json")
    require(len(old_ids) == len(set(old_ids)) == 5536, "precisely 5536 old partial IDs")
    payload = gzip.decompress((ROOT / catalog["catalog_path"]).read_bytes())
    require(sha256(payload).hexdigest() == catalog["catalog_uncompressed_sha256"], "payload pin")
    require(len(payload) == 196992 * 40, "full packed catalog")
    for old_id, old in enumerate(load(OLD / "partial-catalog.json")):
        require(old["partial_id"] == old_id, "old partial order")
        require(
            tuple(old["global_block_ids"])
            == struct.unpack_from("<20H", payload, 40 * old_ids[old_id]),
            "old family match",
        )
    new_partials, new_boundaries, full_boundaries = [], [0], [0]
    skipped = set()
    for fiber_id, fiber in enumerate(fibers):
        require(fiber["excess_link_id"] == fiber_id, "fiber order")
        start, stop = fiber["partial_id_range_half_open"]
        require((start, stop) == (5184 * fiber_id, 5184 * (fiber_id + 1)), "fiber partial range")
        profiles = fiber["profile_ids"]
        require(profiles == sorted(set(profiles)), "profile order")
        old = set(fiber["old_partial_ids_in_expanded_catalog"])
        require(old <= set(range(start, stop)) and not skipped.intersection(old), "old fiber IDs")
        skipped.update(old)
        new_partials.append([i for i in range(start, stop) if i not in old])
        require(len(new_partials[-1]) == fiber["new_only_partial_count"], "new fiber count")
        new_boundaries.append(new_boundaries[-1] + len(new_partials[-1]) * len(profiles))
        full_boundaries.append(full_boundaries[-1] + (stop - start) * len(profiles))
    require(skipped == set(old_ids), "exact mapped old family skip set")
    require(new_boundaries[-1] == NEW_TOTAL and full_boundaries[-1] == TOTAL, "exact pair domains")
    require(full_boundaries == catalog["pair_boundaries"], "original full ordinal boundaries")
    require(
        sorted(p for f in fibers for p in f["profile_ids"]) == list(range(1300)),
        "complete profile partition",
    )
    check_time(started)
    triple_rank = {triple: row for row, triple in enumerate(core.TRIPLES)}
    require(len(triple_rank) == 455 and core.BLOCKS[1365:] == core.AVOIDING, "residual domain")
    row_masks = [0] * 455
    for index, block in enumerate(core.AVOIDING):
        for triple in combinations(block, 3):
            row_masks[triple_rank[triple]] |= 1 << index
    require(
        len(core.AVOIDING) == 3003 and all(m.bit_count() == 66 for m in row_masks),
        "all 3003 candidates and all 66 carriers per row",
    )
    profile_masks = []
    for profile in load(OLD / "profiles.json"):
        require(profile["profile_id"] == len(profile_masks), "profile index")
        indices = [triple_rank[tuple(t)] for t in profile["excess_triples"] if 1 not in t]
        require(len(indices) == len(set(indices)) == 65, "outside profile rows")
        profile_masks.append(sum(1 << i for i in indices))
    require(len(profile_masks) == 1300, "all profiles loaded")
    check_time(started)
    return {
        "core": core,
        "payload": payload,
        "triple_rank": triple_rank,
        "new_partials": new_partials,
        "new_boundaries": new_boundaries,
        "data": {
            "fibers": fibers,
            "boundaries": full_boundaries,
            "row_masks": row_masks,
            "profile_masks": profile_masks,
            "partial_masks": {},
            "partial_indices": {},
        },
    }


def locate_new(context, new_index):
    require(type(new_index) is int and 0 <= new_index < NEW_TOTAL, "new-only pair index")
    fiber_id = bisect.bisect_right(context["new_boundaries"], new_index) - 1
    fiber = context["data"]["fibers"][fiber_id]
    local = new_index - context["new_boundaries"][fiber_id]
    partial_offset, profile_offset = divmod(local, len(fiber["profile_ids"]))
    partial_id = context["new_partials"][fiber_id][partial_offset]
    ordinal = (
        context["data"]["boundaries"][fiber_id]
        + (partial_id - fiber["partial_id_range_half_open"][0]) * len(fiber["profile_ids"])
        + profile_offset
    )
    return fiber_id, partial_id, fiber["profile_ids"][profile_offset], ordinal


def prepare_partial(context, partial_id):
    data = context["data"]
    if partial_id in data["partial_masks"]:
        return
    ids = struct.unpack_from("<20H", context["payload"], partial_id * 40)
    require(len(set(ids)) == 20 and ids == tuple(sorted(ids)) and max(ids) < 1365, "partial IDs")
    rows = sorted(
        context["triple_rank"][triple]
        for i in ids
        for triple in combinations(context["core"].BLOCKS[i][1:], 3)
    )
    require(len(rows) == len(set(rows)) == 80, "eighty distinct outside triples")
    data["partial_masks"] = {partial_id: sum(1 << row for row in rows)}
    data["partial_indices"] = {partial_id: rows}


def next_cursor(context, new_index):
    return {
        "next_new_pair_index": new_index,
        "next_full_pair_ordinal": None
        if new_index == NEW_TOTAL
        else locate_new(context, new_index)[3],
    }


class CommittedWriter:
    """The atomic cursor, not file length or ledger tails, defines durable evidence."""

    def __init__(self, raw, manifest_hash, source_hash, context):
        require(not raw.exists(), "no retry or resume of an existing raw directory")
        raw.mkdir(parents=True)
        self.raw = raw
        self.context = context
        self.cases = (raw / "cases.jsonl.gz").open("wb")
        self.survivors = (raw / "survivors.jsonl.gz").open("wb")
        self.ledger = (raw / "commits.jsonl").open("wb")
        self.hashes = {name: sha256() for name in ("cases", "survivors", "ledger")}
        self.cursor = {
            "schema": "affine-gzip-commits-v1",
            "manifest_sha256": manifest_hash,
            "source_sha256": source_hash,
            "committed_batches": 0,
            "committed_cases": 0,
            "outcomes": {},
            "operation_counts": {},
            "files": {
                name: {"bytes": 0, "sha256": sha256(b"").hexdigest()} for name in self.hashes
            },
            **next_cursor(context, 0),
        }
        atomic_json(raw / "cursor.json", self.cursor)

    def commit(self, rows, outcomes, operations):
        require(0 < len(rows) <= BATCH_SIZE, "bounded nonempty commit batch")
        first = rows[0]["new_pair_index"]
        require(first == self.cursor["committed_cases"], "contiguous new-only prefix")
        require(
            [row["new_pair_index"] for row in rows] == list(range(first, first + len(rows))),
            "ordered batch",
        )
        case_payload = b"".join(encoded(row) for row in rows)
        survivor_payload = b"".join(
            encoded(row) for row in rows if row["outcome"] == "survives_single_pass"
        )
        members = {}
        for name, stream, payload in (
            ("cases", self.cases, case_payload),
            ("survivors", self.survivors, survivor_payload),
        ):
            member = gzip.compress(payload, compresslevel=6, mtime=0)
            start = stream.tell()
            stream.write(member)
            stream.flush()
            os.fsync(stream.fileno())
            self.hashes[name].update(member)
            members[name] = {
                "start_byte": start,
                "end_byte": stream.tell(),
                "compressed_sha256": sha256(member).hexdigest(),
                "uncompressed_sha256": sha256(payload).hexdigest(),
            }
        entry = {
            "batch_index": self.cursor["committed_batches"],
            "new_pair_range_half_open": [first, first + len(rows)],
            "first_full_pair_ordinal": rows[0]["pair_ordinal"],
            "last_full_pair_ordinal": rows[-1]["pair_ordinal"],
            "cases": len(rows),
            "survivors": sum(row["outcome"] == "survives_single_pass" for row in rows),
            "members": members,
        }
        line = encoded(entry)
        self.ledger.write(line)
        self.ledger.flush()
        os.fsync(self.ledger.fileno())
        self.hashes["ledger"].update(line)
        candidate = dict(self.cursor)
        candidate.update(
            {
                "committed_batches": self.cursor["committed_batches"] + 1,
                "committed_cases": first + len(rows),
                "outcomes": dict(outcomes),
                "operation_counts": dict(operations),
                "last_commit_sha256": sha256(line).hexdigest(),
                "files": {
                    name: {"bytes": stream.tell(), "sha256": self.hashes[name].hexdigest()}
                    for name, stream in (
                        ("cases", self.cases),
                        ("survivors", self.survivors),
                        ("ledger", self.ledger),
                    )
                },
                **next_cursor(self.context, first + len(rows)),
            }
        )
        atomic_json(self.raw / "cursor.json", candidate)
        self.cursor = candidate

    def close(self):
        for stream in (self.cases, self.survivors, self.ledger):
            stream.close()


def terminate(_signum, _frame):
    global TERMINATE_REQUESTED
    TERMINATE_REQUESTED = True


def run():
    require("AFFINE_FULL_STARTED_MONOTONIC" in os.environ, "use the gated watchdog launcher")
    started = float(os.environ["AFFINE_FULL_STARTED_MONOTONIC"])
    require(0 <= time.monotonic() - started < 660, "shared launcher budget clock")
    require(not (HERE / "result.json").exists() and not RAW.exists(), "no retry or resume")
    signal.signal(signal.SIGTERM, terminate)
    manifest = load(HERE / "manifest.json")
    check_gate(manifest)
    writer, context = None, None
    outcomes, operations = Counter(), Counter()
    rows, processed = [], 0
    error = None
    status = "cooperative_timeout"
    try:
        context = load_frozen(manifest, started)
        writer = CommittedWriter(RAW, sha(HERE / "manifest.json"), sha(__file__), context)
        while processed < NEW_TOTAL:
            if time.monotonic() - started >= STOP_NEW_SECONDS or TERMINATE_REQUESTED:
                break
            fiber_id, partial_id, profile_id, ordinal = locate_new(context, processed)
            prepare_partial(context, partial_id)
            if time.monotonic() - started >= STOP_NEW_SECONDS or TERMINATE_REQUESTED:
                break
            row = context["core"].screen(context["data"], ordinal)
            require(
                row["partial_id"] == partial_id and row["profile_id"] == profile_id,
                "unchanged core agrees with new-only mapping",
            )
            row.update({"new_pair_index": processed, "excess_link_id": fiber_id})
            rows.append(row)
            outcomes[row["outcome"]] += 1
            operations.update(row["operation_counts"])
            processed += 1
            if len(rows) == BATCH_SIZE:
                writer.commit(rows, outcomes, operations)
                rows = []
        if rows:
            writer.commit(rows, outcomes, operations)
            rows = []
        status = "complete" if processed == NEW_TOTAL else "cooperative_timeout"
        if TERMINATE_REQUESTED:
            status = "external_termination"
    except TimeoutError as failure:
        error = str(failure)
    except Exception as failure:
        status, error = "error", f"{type(failure).__name__}: {failure}"
    finally:
        if writer is not None:
            writer.close()
    elapsed = time.monotonic() - started
    within_budget = elapsed < COOPERATIVE_SECONDS
    if status == "complete" and not within_budget:
        status = "complete_over_cooperative_budget"
    result = {
        "status": status,
        "error": error,
        "new_pairs": NEW_TOTAL,
        "evaluated_cases": processed,
        "committed_cursor": None if writer is None else writer.cursor,
        "uncommitted_evaluations": processed
        - (0 if writer is None else writer.cursor["committed_cases"]),
        "elapsed_before_receipt_seconds": elapsed,
        "within_cooperative_budget_before_receipt": within_budget,
        "source_sha256": sha(__file__),
        "manifest_sha256": sha(HERE / "manifest.json"),
        "gate_sha256": sha(GATE),
        "optimizer_calls": 0,
        "automatic_retry": False,
        "automatic_resume": False,
    }
    atomic_json(HERE / "result.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "committed_cursor"}, sort_keys=True))
    return 0 if status == "complete" else (1 if status == "error" else 124)


if __name__ == "__main__":
    require(len(sys.argv) == 2 and sys.argv[1] in ("prepare", "run"), "explicit mode")
    if sys.argv[1] == "prepare":
        prepare()
    else:
        sys.exit(run())
