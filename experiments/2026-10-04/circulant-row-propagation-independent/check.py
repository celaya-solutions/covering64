# Document:    Independent Circulant Row Propagation Trace Checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      010823b8c0f99d71d8d8a956367e50d170f9e8a05000a50a83525f6d61386a41
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay saved deductions using independently reconstructed Python sets."""

import copy
import gzip
import json
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BENCH = ROOT / "experiments/2026-10-04/circulant-chosen-link-row-propagation"
CAT = ROOT / "experiments/2026-10-04/circulant-chosen-link-catalog"
TRIPLES = list(combinations(range(2, 17), 3))
BLOCKS = list(combinations(range(1, 17), 5))
DOMAIN = set(range(1365, 4368))


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def context():
    rank = {b: i for i, b in enumerate(BLOCKS)}
    rows = []
    for triple in TRIPLES:
        others = [v for v in range(2, 17) if v not in triple]
        row = {rank[tuple(sorted(triple + extra))] for extra in combinations(others, 2)}
        assert len(row) == 66 and row <= DOMAIN
        rows.append(row)
    rows.append(DOMAIN)
    profiles = json.loads((CAT / "profiles.json").read_text())
    partials = json.loads((CAT / "partial-catalog.json").read_text())
    excess = [{tuple(t) for t in p["excess_triples"]} for p in profiles]
    fixed = [
        Counter(t for i in p["global_block_ids"] for t in combinations(BLOCKS[i], 3))
        for p in partials
    ]
    return rows, excess, fixed


def bitmap_hash(ids):
    value = sum(1 << (i - 1365) for i in ids)
    return sha256(value.to_bytes(376, "little")).hexdigest()


def check(record, ctx):
    rows, profiles, partials = ctx
    excess, fixed = profiles[record["profile_id"]], partials[record["partial_id"]]
    demands = [1 + (t in excess) - fixed[t] for t in TRIPLES] + [44]
    assert min(demands) >= 0 and sum(demands[:-1]) == 440
    assert record["initial_domain_count"] == 3003 and record["exact_row_count"] == 456
    selected, removed = set(), set()
    for step in record["trace"]:
        row, value, ids = step["row"], step["value"], step["global_ids"]
        assert type(row) is int and 0 <= row < 456
        assert type(value) is int and value in (0, 1)
        assert all(type(i) is int for i in ids) and ids == sorted(set(ids))
        present = rows[row] & selected
        free = rows[row] - selected - removed
        assert free and ids == sorted(free)
        assert len(present) <= demands[row] <= len(present) + len(free)
        assert (
            len(present) == demands[row]
            if value == 0
            else (len(present) + len(free) == demands[row])
        )
        (removed if value == 0 else selected).update(free)
        assert not selected & removed and (selected | removed) <= DOMAIN
    assert record["selected_global_ids"] == sorted(selected)
    assert record["selected_count"] == len(selected) and record["removed_count"] == len(removed)
    assert record["selected_mask_sha256"] == bitmap_hash(selected)
    assert record["removed_mask_sha256"] == bitmap_hash(removed)
    outcome = record["outcome"]
    if outcome == "contradiction":
        evidence = record["final_evidence"]
        row = evidence["row"]
        assert type(row) is int and 0 <= row < 456
        present = rows[row] & selected
        free = rows[row] - selected - removed
        assert len(present) > demands[row] or len(present) + len(free) < demands[row]
        assert evidence == {
            "row": row,
            "demand": demands[row],
            "selected_count": len(present),
            "free_count": len(free),
            "selected_global_ids": sorted(present),
            "free_global_ids": sorted(free),
        }
    else:
        assert outcome == "survives_row_propagation" and record["final_evidence"] is None
        assert len(selected) < 44
        for row, demand in zip(rows, demands):
            count = len(row & selected)
            available = len(row - selected - removed)
            assert count <= demand <= count + available
            assert not available or (count != demand and count + available != demand)
    return outcome, len(record["trace"])


def main():
    receipt = json.loads((BENCH / "benchmark.json").read_text())
    manifest = json.loads((BENCH / "manifest.json").read_text())
    assert sha(BENCH / "benchmark.json") == (
        "1c1320160351c5d5ddfa0df5b10475846a444e6d58035e3a6621fafbb6572fa1"
    )
    assert sha(BENCH / "manifest.json") == receipt["manifest_sha256"]
    assert sha(BENCH / "run.py") == receipt["source_sha256"] == manifest["source_sha256"]
    for p, h in manifest["dependencies"].items():
        assert sha(ROOT / p) == h
    trace = ROOT / receipt["trace_file"]
    assert sha(trace) == receipt["trace_file_sha256"]
    with gzip.open(trace, "rt") as stream:
        records = [json.loads(line) for line in stream]
    assert len(records) == receipt["completed_cases"] == 1000
    assert receipt["complete_benchmark"] is True
    assert [r["pair_ordinal"] for r in records] == receipt["completed_pair_ordinals"]
    assert [r["pair_ordinal"] for r in records] == manifest["benchmark_pair_ordinals"]
    assert [r["survivor_index"] for r in records] == manifest["benchmark_survivor_indices"]
    assert [r["benchmark_position"] for r in records] == list(range(1000))
    full = json.loads(
        (
            ROOT / ("experiments/2026-10-04/circulant-chosen-link-support-full/result.json")
        ).read_text()
    )
    survivor_path = ROOT / full["survivor_records"]
    assert sha(survivor_path) == full["survivor_records_sha256"]
    with gzip.open(survivor_path, "rt") as stream:
        survivors = [json.loads(line) for line in stream]
    assert len(survivors) == 10228
    sample = [(i * 10228) // 1000 for i in range(1000)]
    assert manifest["benchmark_survivor_indices"] == sample
    fibers = json.loads((CAT / "link-fibers.json").read_text())
    pair_order = [
        (p, q)
        for fiber in fibers
        for p in range(*fiber["partial_id_range_half_open"])
        for q in fiber["profile_ids"]
    ]
    assert len(pair_order) == 195296
    for record, index in zip(records, sample):
        assert all(
            record[key] == survivors[index][key]
            for key in ("pair_ordinal", "partial_id", "profile_id")
        )
        assert (record["partial_id"], record["profile_id"]) == pair_order[record["pair_ordinal"]]
    ctx = context()
    outcomes = Counter()
    steps = 0
    for record in records:
        outcome, n = check(record, ctx)
        outcomes[outcome] += 1
        steps += n
    assert dict(outcomes) == receipt["outcomes"] and steps == receipt["total_forcing_steps"]
    damaged = []
    for damage in (
        "flipped_value",
        "omitted_literal",
        "wrong_row",
        "bool_value",
        "final_demand",
        "removed_hash",
        "survivor_omitted_step",
    ):
        r = copy.deepcopy(
            next(
                r
                for r in records
                if r["outcome"]
                == (
                    "survives_row_propagation"
                    if damage == "survivor_omitted_step"
                    else "contradiction"
                )
            )
        )
        if damage == "flipped_value":
            r["trace"][0]["value"] ^= 1
        elif damage == "omitted_literal":
            r["trace"][0]["global_ids"].pop()
        elif damage == "wrong_row":
            r["trace"][0]["row"] = 455
        elif damage == "bool_value":
            r["trace"][0]["value"] = False
        elif damage == "final_demand":
            r["final_evidence"]["demand"] += 1
        elif damage == "removed_hash":
            r["removed_mask_sha256"] = "0" * 64
        else:
            r["trace"].pop()
        try:
            check(r, ctx)
        except AssertionError:
            damaged.append(damage)
        else:
            raise AssertionError("Accepted damaged proof: " + damage)
    audit = {
        "passed": True,
        "source_sha256": sha(Path(__file__)),
        "benchmark_sha256": sha(BENCH / "benchmark.json"),
        "manifest_sha256": sha(BENCH / "manifest.json"),
        "trace_sha256": sha(trace),
        "cases": 1000,
        "outcomes": dict(outcomes),
        "force_steps_replayed": steps,
        "damage_controls_rejected": damaged,
        "engine": "Independent row sets and direct integer bounds; no producer import",
        "optimizer_calls": 0,
        "search_calls": 0,
        "scope": "Saved1000-case benchmark traces only; not the full10228 survivors",
    }
    (HERE / "benchmark-audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "outcomes": dict(outcomes),
                "steps": steps,
                "audit_sha256": sha(HERE / "benchmark-audit.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
