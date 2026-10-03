#!/usr/bin/env python3
# Document:    Independent Exact Weighted Enumeration of Residual Core Kernels
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      2e0f71cc56da6df00559f40a1826ce2071ca23190c22b00d34bbb120e0801701
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Audit and enumerate specified retained-core neighborhoods using only stdlib.

All arithmetic is integer arithmetic in units of the supplied denominator D.
If total positive triple weight is S and m blocks are allowed, any completion
has cumulative loss k*D minus the weight of the union covered so far at most
m*D-S. Every next block contributes nonnegative loss because every universe
block has weight at most D. Thus no branch removed by this test can complete.

The initial pool is independently rebuilt: each selected block must have load
at least S-(m-1)*D, because the other m-1 blocks have load at most D each.
Here S>(m-1)*D, so fewer than m blocks cannot cover the positive weight.

At every nonterminal state we choose an uncovered residual triple and branch
over ALL remaining pool blocks containing it that pass the loss test. This
includes zero-weight triples. Any valid extension has at least one such block;
branching in this way is complete even though different orders can repeat a
set. A tree is conclusive only when every branch was exhausted. All claims
are confined to the explicit fixed retained blocks in each input case.
"""

import argparse
import gzip
import hashlib
import itertools
import json
import platform
import subprocess
import time
from fractions import Fraction
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value):
    return type(value) is int


def bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def universe():
    triples = list(itertools.combinations(range(1, 17), 3))
    blocks = list(itertools.combinations(range(1, 17), 5))
    ranks = {triple: rank for rank, triple in enumerate(triples)}
    block_triples = [
        tuple(ranks[t] for t in itertools.combinations(block, 3))
        for block in blocks
    ]
    block_masks = [sum(1 << t for t in ts) for ts in block_triples]
    require(len(blocks) == 4368 and len(triples) == 560, "universe size")
    return triples, blocks, block_triples, block_masks


def audit_case(case, m, blocks, block_triples, block_masks):
    retained = case["retained_block_ids"]
    require(isinstance(retained, list), "retained IDs must be a list")
    require(all(integer(x) and 0 <= x < 4368 for x in retained), "retained ID")
    require(len(retained) == len(set(retained)), "duplicate retained block")
    require(retained == sorted(retained), "retained blocks not lexicographic")
    require([list(blocks[x]) for x in retained] == case["retained_core_blocks"],
            "retained explicit blocks mismatch")
    require(len(retained) + m == 64, "neighborhood size does not total 64")
    denominator = case["denominator"]
    require(integer(denominator) and denominator > 0, "bad denominator")
    retained_coverage = 0
    for bid in retained:
        retained_coverage |= block_masks[bid]
    missing = ((1 << 560) - 1) ^ retained_coverage
    weights = [0] * 560
    require(isinstance(case["weights"], list), "weights must be a list")
    for pair in case["weights"]:
        require(isinstance(pair, list) and len(pair) == 2, "bad weight pair")
        tid, weight = pair
        require(integer(tid) and 0 <= tid < 560, "bad weighted triple")
        require(integer(weight) and weight > 0, "nonpositive weight")
        require(weights[tid] == 0, "duplicate weighted triple")
        require(bool(missing & (1 << tid)), "weight on retained covered triple")
        weights[tid] = weight
    total = sum(weights)
    bound = Fraction(total, denominator)
    require([bound.numerator, bound.denominator] == case["exact_lower_bound"],
            "reported bound mismatch")
    require((m - 1) * denominator < total <= m * denominator,
            "unsupported bound: expected m-1 < B <= m")
    capacities = [sum(weights[t] for t in ts) for ts in block_triples]
    require(max(capacities) <= denominator, "dual infeasible on universe")
    cutoff = total - (m - 1) * denominator
    pool = [bid for bid, cap in enumerate(capacities) if cap >= cutoff]
    require(pool == case["allowed_block_ids"], "incomplete or wrong reduced pool")
    require([list(blocks[x]) for x in pool] == case["allowed_blocks"],
            "pool explicit blocks mismatch")
    require(len(pool) == case["allowed_block_count"], "pool count mismatch")
    require(cutoff == case["minimum_block_load_numerator"], "pool cutoff mismatch")
    require(not set(pool).intersection(retained), "pool contains retained block")
    return {
        "retained": retained, "weights": weights, "denominator": denominator,
        "total": total, "missing": missing, "capacities": capacities,
        "pool": pool, "cutoff": cutoff,
    }


def enumerate_case(case_index, case, audit, m, block_masks, blocks,
                   max_nodes, max_seconds):
    start = time.monotonic()
    deadline = start + max_seconds
    denominator = audit["denominator"]
    slack = m * denominator - audit["total"]
    weights = audit["weights"]
    pool = audit["pool"]
    supports = [[] for _ in range(560)]
    masks = {bid: block_masks[bid] & audit["missing"] for bid in pool}
    for bid in pool:
        for tid in bits(masks[bid]):
            supports[tid].append(bid)
    trace = []
    witness = None

    def visit(uncovered, selected, covered_weight):
        nonlocal witness
        if len(trace) >= max_nodes or time.monotonic() >= deadline:
            return None, "UNKNOWN"
        nid = len(trace)
        loss = len(selected) * denominator - covered_weight
        node = {
            "id": nid, "selected_block_ids": list(selected),
            "uncovered_mask_hex": hex(uncovered),
            "covered_weight_numerator": covered_weight,
            "loss_numerator": loss,
        }
        trace.append(node)
        require(loss <= slack, "internal loss invariant")
        if not uncovered:
            full = sorted(audit["retained"] + list(selected))
            require(len(full) <= 64 and len(set(full)) == len(full), "bad witness IDs")
            covered = 0
            for bid in full:
                covered |= block_masks[bid]
            require(covered == (1 << 560) - 1, "bad full witness coverage")
            witness = {"block_ids": full, "blocks": [list(blocks[b]) for b in full]}
            node["status"] = "COVER_FOUND"
            return nid, "COVER_FOUND"
        if len(selected) == m:
            node["status"] = "EXHAUSTED_DEPTH"
            return nid, "EXHAUSTED"
        remaining_slack = slack - loss
        chosen = set(selected)
        eligible = {}
        for bid in pool:
            if bid in chosen:
                continue
            newly = masks[bid] & uncovered
            new_weight = sum(weights[t] for t in bits(newly))
            cost = denominator - new_weight
            require(cost >= 0, "negative incremental loss")
            if cost <= remaining_slack:
                eligible[bid] = new_weight
        tid, options = min(
            ((t, [bid for bid in supports[t] if bid in eligible])
             for t in bits(uncovered)),
            key=lambda item: (len(item[1]), item[0]),
        )
        node["branch_triple_id"] = tid
        node["eligible_block_ids"] = options
        if not options:
            node["status"] = "EXHAUSTED_NO_ELIGIBLE_BLOCK"
            return nid, "EXHAUSTED"
        node["children"] = []
        for bid in options:
            child_id, status = visit(
                uncovered & ~masks[bid], selected + (bid,),
                covered_weight + eligible[bid],
            )
            node["children"].append({"block_id": bid, "node_id": child_id,
                                     "status": status})
            if status != "EXHAUSTED":
                node["status"] = status
                return nid, status
        node["status"] = "EXHAUSTED"
        return nid, "EXHAUSTED"

    _, status = visit(audit["missing"], (), 0)
    return {
        "case_index": case_index, "removed_core_positions": case["removed"],
        "input_case_sha256": digest(case),
        "status": status, "seconds": time.monotonic() - start,
        "node_count": len(trace), "pool_count": len(pool),
        "residual_triple_count": audit["missing"].bit_count(),
        "dual_bound": [Fraction(audit["total"], denominator).numerator,
                       Fraction(audit["total"], denominator).denominator],
        "denominator": denominator, "slack_numerator": slack,
        "cutoff_numerator": audit["cutoff"],
        "all_4368_capacity_numerators": audit["capacities"],
        "capacities_sha256": digest(audit["capacities"]),
        "trace": trace, "trace_sha256": digest(trace), "witness": witness,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--nodes", type=int, default=250_000)
    parser.add_argument("--seconds", type=float, default=5.0)
    args = parser.parse_args()
    require(args.nodes > 0 and args.seconds > 0, "positive budgets required")
    require(not args.output.exists(), "refusing to overwrite output")
    raw = args.input.read_bytes()
    data = json.loads(gzip.decompress(raw) if args.input.suffix == ".gz" else raw)
    m = data["additional_blocks_allowed"]
    require(integer(m) and m > 0, "invalid block budget")
    triples, blocks, block_triples, block_masks = universe()
    results = []
    start = time.monotonic()
    for index, case in enumerate(data["candidates"]):
        audit = audit_case(case, m, blocks, block_triples, block_masks)
        result = enumerate_case(index, case, audit, m, block_masks, blocks,
                                args.nodes, args.seconds)
        results.append(result)
        print(json.dumps({k: result[k] for k in [
            "case_index", "removed_core_positions", "status", "node_count",
            "seconds", "pool_count", "residual_triple_count", "dual_bound",
        ]}), flush=True)
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = None
    body = {
        "format": "covering64-independent-weighted-tree-v1",
        "scope": "Only the explicit retained-block neighborhoods in the input; no global claim",
        "input_path": str(args.input), "input_sha256": hashlib.sha256(raw).hexdigest(),
        "input_json_sha256": digest(data),
        "source_revision": revision,
        "enumerator_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python_version": platform.python_version(), "platform": platform.platform(),
        "solver": "stdlib exact integer weighted DFS; no external solver or package code",
        "seeds": [],
        "deterministic_branch_order": (
            "minimum eligible support; triple rank tie; block rank order"
        ),
        "per_case_node_budget": args.nodes, "per_case_seconds_budget": args.seconds,
        "additional_blocks_allowed": m, "universe_block_count": len(blocks),
        "universe_triple_count": len(triples),
        "universe_blocks_sha256": digest(blocks), "universe_triples_sha256": digest(triples),
        "elapsed_seconds": time.monotonic() - start, "results": results,
    }
    output = {"document_header": {
        "Document": "Independent Residual Kernel Enumeration and Full Search Traces",
        "Version": "v1.0.0", "Author": "Celaya Solutions",
        "Contact": "hello@celayasolutions.com", "Date": "2026-10-03",
        "SHA256": digest(body), "Chain": "n/a", "Tx": "[not anchored]",
        "License": "All Rights Reserved / Celaya Solutions",
    }, "body": body}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = canonical(output) + b"\n"
    args.output.write_bytes(gzip.compress(encoded, mtime=0)
                            if args.output.suffix == ".gz" else encoded)
    print(json.dumps({"output": str(args.output),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
                      "counts": {s: sum(r["status"] == s for r in results)
                                 for s in ["EXHAUSTED", "UNKNOWN", "COVER_FOUND"]},
                      "nodes": sum(r["node_count"] for r in results)}), flush=True)


if __name__ == "__main__":
    main()
