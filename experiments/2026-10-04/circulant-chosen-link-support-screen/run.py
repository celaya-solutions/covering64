# Document:    One Pass Support Screen for Chosen Circulant Point Links
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      2944e13a78fb2f0bbd7a211204cd5a79943029b712b1606daec0e4032dfdd377
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare or benchmark a finite one-pass screen; never invoke an optimizer."""

from __future__ import annotations

import bisect
import gzip
import io
import json
import subprocess
import sys
import time
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CATALOG = HERE.parent / "circulant-chosen-link-catalog"
RAW = ROOT / "experiments/scratch/circulant-chosen-link-support-v1.0.0"
TOTAL = 195296
BENCHMARK_CASES = 1000
BENCHMARK_SECONDS = 10.0
BLOCKS = tuple(combinations(range(1, 17), 5))
AVOIDING = tuple(combinations(range(2, 17), 5))
TRIPLES = tuple(combinations(range(2, 17), 3))
OFFSET = 1365
ALL = (1 << 3003) - 1


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def global_ids(mask):
    result = []
    while mask:
        low = mask & -mask
        result.append(OFFSET + low.bit_length() - 1)
        mask -= low
    return result


def prepare():
    require(not (HERE / "manifest.json").exists(), "fresh preparation only")
    catalog_pins = json.loads((CATALOG / "files.json").read_text())
    for name, expected in catalog_pins.items():
        require(sha(CATALOG / name) == expected, "catalog pin")
    summary = json.loads((CATALOG / "summary.json").read_text())
    require(summary["profile_link_pairs"] == TOTAL, "full pair count")
    sample = [(index * TOTAL) // BENCHMARK_CASES for index in range(BENCHMARK_CASES)]
    require(len(set(sample)) == BENCHMARK_CASES and sample[-1] < TOTAL, "fixed benchmark sample")
    dump(
        HERE / "manifest.json",
        {
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "source_sha256": sha(__file__),
            "inputs": {
                str((CATALOG / name).relative_to(ROOT)): expected
                for name, expected in catalog_pins.items()
            },
            "catalog_files_sha256": sha(CATALOG / "files.json"),
            "benchmark_cases": BENCHMARK_CASES,
            "benchmark_seconds": BENCHMARK_SECONDS,
            "benchmark_pair_ordinals": sample,
            "full_pair_count": TOTAL,
            "pair_order": "excess_link_id, then partial_id, then the fiber's ascending profile_id",
            "remaining_domain": "All3003 point-one-avoiding pentads; globalIDs1365..4367.",
            "rows": "455 lexicographic triples on2..16 plus exact remaining cardinality44.",
            "stage": "one support pass and one immediate forced-conflict check; no iteration",
            "full_run_authorized": False,
            "full_run_wall_budget_seconds": None,
            "optimizer_calls": 0,
            "scope": (
                "Only all E_p-isomorphism images of the four chosen saved point links, "
                "across the supplied1300profiles."
            ),
        },
    )
    print(
        json.dumps(
            {
                "prepared": True,
                "manifest_sha256": sha(HERE / "manifest.json"),
                "screening_launched": False,
            }
        )
    )


def load_frozen():
    manifest = json.loads((HERE / "manifest.json").read_text())
    require(sha(__file__) == manifest["source_sha256"], "runner pin")
    require(sha(CATALOG / "files.json") == manifest["catalog_files_sha256"], "catalog index pin")
    for path, expected in manifest["inputs"].items():
        require(sha(ROOT / path) == expected, "catalog file pin")
    fibers = json.loads((CATALOG / "link-fibers.json").read_text())
    partials = json.loads((CATALOG / "partial-catalog.json").read_text())
    profiles = json.loads((CATALOG / "profiles.json").read_text())
    triple_rank = {triple: index for index, triple in enumerate(TRIPLES)}
    require(BLOCKS[OFFSET:] == AVOIDING and len(AVOIDING) == 3003, "global ID offset")
    row_masks = [0] * 455
    for index, block in enumerate(AVOIDING):
        for triple in combinations(block, 3):
            row_masks[triple_rank[triple]] |= 1 << index
    require(all(mask.bit_count() == 66 for mask in row_masks), "complete triple supports")
    profile_masks = []
    for profile in profiles:
        indices = [triple_rank[tuple(row)] for row in profile["excess_triples"] if 1 not in row]
        require(len(indices) == len(set(indices)) == 65, "outside profile triples")
        profile_masks.append(sum(1 << index for index in indices))
    partial_masks = []
    partial_indices = []
    for partial in partials:
        triples = [
            triple
            for index in partial["global_block_ids"]
            for triple in combinations(BLOCKS[index][1:], 3)
        ]
        require(len(triples) == len(set(triples)) == 80, "outside partial triples")
        indices = sorted(triple_rank[triple] for triple in triples)
        partial_indices.append(indices)
        partial_masks.append(sum(1 << index for index in indices))
    boundaries = [0]
    for fiber in fibers:
        start, stop = fiber["partial_id_range_half_open"]
        boundaries.append(boundaries[-1] + (stop - start) * len(fiber["profile_ids"]))
    require(boundaries[-1] == TOTAL, "full deterministic pair order")
    return {
        "manifest": manifest,
        "fibers": fibers,
        "boundaries": boundaries,
        "row_masks": row_masks,
        "profile_masks": profile_masks,
        "partial_masks": partial_masks,
        "partial_indices": partial_indices,
    }


def locate(data, ordinal):
    require(type(ordinal) is int and 0 <= ordinal < TOTAL, "pair ordinal")
    fiber_id = bisect.bisect_right(data["boundaries"], ordinal) - 1
    fiber = data["fibers"][fiber_id]
    local = ordinal - data["boundaries"][fiber_id]
    partial_offset, profile_offset = divmod(local, len(fiber["profile_ids"]))
    return fiber["partial_id_range_half_open"][0] + partial_offset, fiber["profile_ids"][
        profile_offset
    ]


def screen(data, ordinal):
    partial_id, profile_id = locate(data, ordinal)
    profile = data["profile_masks"][profile_id]
    covered = data["partial_masks"][partial_id]
    residual = [1 + ((profile >> row) & 1) - ((covered >> row) & 1) for row in range(455)]
    require(min(residual) >= 0 and sum(residual) == 440, "exact residual rows")
    active = ALL
    zero_rows = [row for row in data["partial_indices"][partial_id] if not (profile >> row) & 1]
    for row in zero_rows:
        active &= ~data["row_masks"][row]
    active_count = active.bit_count()
    output = {
        "pair_ordinal": ordinal,
        "partial_id": partial_id,
        "profile_id": profile_id,
        "initial_domain_count": 3003,
        "eligible_candidates": active_count,
        "eligible_mask_sha256": sha256(active.to_bytes(376, "little")).hexdigest(),
    }
    counters = {
        "zero_row_unions": len(zero_rows),
        "support_row_popcounts": 0,
        "conflict_row_popcounts": 0,
        "cardinality_support_checks": 1,
    }
    output["operation_counts"] = counters
    if active_count < 44:
        output.update(
            {
                "outcome": "insufficient_support",
                "row": 455,
                "demand": 44,
                "support_global_ids": global_ids(active),
            }
        )
        return output
    forced = 0
    causes = {}
    if active_count == 44:
        forced = active
        causes = {index: 455 for index in global_ids(active)}
    for row, demand in enumerate(residual):
        if demand == 0:
            continue
        support = active & data["row_masks"][row]
        count = support.bit_count()
        counters["support_row_popcounts"] += 1
        if count < demand:
            output.update(
                {
                    "outcome": "insufficient_support",
                    "row": row,
                    "triple": TRIPLES[row],
                    "demand": demand,
                    "support_global_ids": global_ids(support),
                }
            )
            return output
        if count == demand:
            forced |= support
            for index in global_ids(support):
                causes.setdefault(index, row)
    if forced:
        for row, demand in enumerate(residual):
            selected = forced & data["row_masks"][row]
            counters["conflict_row_popcounts"] += 1
            if selected.bit_count() > demand:
                forced_ids = global_ids(selected)
                evidence = []
                for index in forced_ids:
                    cause = causes[index]
                    support = active if cause == 455 else active & data["row_masks"][cause]
                    evidence.append(
                        {
                            "global_block_id": index,
                            "row": cause,
                            "demand": 44 if cause == 455 else residual[cause],
                            "support_global_ids": global_ids(support),
                        }
                    )
                output.update(
                    {
                        "outcome": "forced_conflict",
                        "row": row,
                        "triple": TRIPLES[row],
                        "demand": demand,
                        "forced_global_ids": forced_ids,
                        "forcing_rows": evidence,
                    }
                )
                return output
        if forced.bit_count() > 44:
            evidence = []
            for index in global_ids(forced):
                cause = causes[index]
                support = active if cause == 455 else active & data["row_masks"][cause]
                evidence.append(
                    {
                        "global_block_id": index,
                        "row": cause,
                        "demand": 44 if cause == 455 else residual[cause],
                        "support_global_ids": global_ids(support),
                    }
                )
            output.update(
                {
                    "outcome": "forced_conflict",
                    "row": 455,
                    "demand": 44,
                    "forced_global_ids": global_ids(forced),
                    "forcing_rows": evidence,
                }
            )
            return output
    output.update(
        {"outcome": "survives_single_pass", "immediately_forced_blocks": forced.bit_count()}
    )
    return output


def benchmark():
    started = time.monotonic()
    require(
        not (HERE / "benchmark.json").exists() and not (RAW / "benchmark").exists(),
        "one fresh benchmark",
    )
    data = load_frozen()
    sample = data["manifest"]["benchmark_pair_ordinals"]
    require(len(sample) == BENCHMARK_CASES, "fixed benchmark size")
    destination = RAW / "benchmark"
    destination.mkdir(parents=True)
    output_path = destination / "cases.jsonl.gz"
    outcomes = Counter()
    operations = Counter()
    completed = []
    loop_started = time.monotonic()
    with (
        output_path.open("xb") as raw,
        gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed,
        io.TextIOWrapper(compressed) as text,
    ):
        for ordinal in sample:
            if time.monotonic() - started >= BENCHMARK_SECONDS - 0.25:
                break
            result = screen(data, ordinal)
            text.write(json.dumps(result, separators=(",", ":"), sort_keys=True) + "\n")
            outcomes[result["outcome"]] += 1
            operations.update(result["operation_counts"])
            completed.append(ordinal)
    elapsed = time.monotonic() - started
    loop_elapsed = time.monotonic() - loop_started
    require(elapsed < BENCHMARK_SECONDS, "benchmark wall cap")
    receipt = {
        "manifest_sha256": sha(HERE / "manifest.json"),
        "source_sha256": sha(__file__),
        "completed_cases": len(completed),
        "requested_cases": BENCHMARK_CASES,
        "complete_benchmark": len(completed) == BENCHMARK_CASES,
        "completed_pair_ordinals": completed,
        "outcomes": dict(outcomes),
        "operation_counts": dict(operations),
        "elapsed_seconds_including_load_and_output": elapsed,
        "case_loop_seconds_including_output": loop_elapsed,
        "case_rate_per_second": len(completed) / loop_elapsed,
        "estimated_full_single_pass_seconds": TOTAL * loop_elapsed / len(completed)
        if completed
        else None,
        "estimate_note": (
            "Fixed stratified1000-pair sample; extrapolation is not a runtime guarantee."
        ),
        "proof_records": str(output_path.relative_to(ROOT)),
        "proof_records_sha256": sha(output_path),
        "full_production_screen_launched": False,
        "iterative_propagation_launched": False,
        "optimizer_calls": 0,
        "scope": "Benchmark of1000 fixed pairs, not a complete195296-pair conclusion.",
    }
    dump(HERE / "benchmark.json", receipt)
    print(
        json.dumps(
            {
                key: receipt[key]
                for key in (
                    "completed_cases",
                    "outcomes",
                    "elapsed_seconds_including_load_and_output",
                    "estimated_full_single_pass_seconds",
                    "full_production_screen_launched",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    if sys.argv[1:] == ["prepare"]:
        prepare()
    elif sys.argv[1:] == ["benchmark"]:
        benchmark()
    else:
        raise SystemExit("Usage: run.py prepare|benchmark; no full-run entrypoint yet")
