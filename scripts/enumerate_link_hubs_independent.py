#!/usr/bin/env python3
# Document:    Independent Complete Residual Link Decomposition Search
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      ab4f066f8d4dcd9407652ec691ce6aad31d6f785284fe087ed3315b2fc1c2016
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Exact integer multicover DFS; no CP, package, or hub-builder imports.

Each row is a distinct four-subset of points 3..16. Every six-pair incidence
is subtracted from the target remaining after the six hub blocks. A row is
eligible precisely when each of its pairs has positive residual demand and
the row is not selected. For a positive-demand pair p, every completion
must use exactly demand[p] eligible rows containing p. Too few rows rejects;
equality forces all of them; otherwise all carriers are branched on. This
enumerates all exact decompositions, possibly visiting a set more than once.
Canonical solution sets remove duplicate visit orders. Budget exhaustion
is UNKNOWN and never proves exhaustion. Full trees are retained per case.
"""

import argparse
import gzip
import hashlib
import itertools
import json
import platform
import subprocess
import time
from collections import Counter
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


def raw_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(raw_json(value)).hexdigest()


def bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask -= bit


def reconstruct(hub):
    require(len(hub) == 6 and len(set(map(tuple, hub))) == 6, "six distinct hub blocks")
    for block in hub:
        require(len(block) == 4 and block == sorted(set(block)), "malformed hub block")
        require(2 in block and all(type(x) is int and 2 <= x <= 16 for x in block),
                "malformed hub labels")
    target = {pair: 1 for pair in itertools.combinations(range(2, 17), 2)}
    for x in range(3, 7):
        target[(2, x)] += 1
    for x in range(7, 17, 2):
        target[(x, x + 1)] += 1
    fixed = Counter(pair for b in hub for pair in itertools.combinations(b, 2))
    remaining = {p: n - fixed[p] for p, n in target.items()}
    require(all(n >= 0 for n in remaining.values()), "hub exceeds pair target")
    require(all(n == 0 for p, n in remaining.items() if 2 in p), "hub not exhausted")
    pairs = list(itertools.combinations(range(3, 17), 2))
    pair_rank = {p: i for i, p in enumerate(pairs)}
    demands = [remaining[p] for p in pairs]
    require(sum(demands) == 78, "residual size")
    require(all(sum(n for p, n in remaining.items() if x in p) % 3 == 0
                for x in range(3, 17)), "residual degree")
    quads = [b for b in itertools.combinations(range(3, 17), 4)
             if all(remaining[p] > 0 for p in itertools.combinations(b, 2))]
    rows = [tuple(pair_rank[p] for p in itertools.combinations(b, 2)) for b in quads]
    supports = [0] * len(pairs)
    for row_id, row in enumerate(rows):
        for p in row:
            supports[p] |= 1 << row_id
    return target, pairs, demands, quads, rows, supports


def enumerate_hub(hub, node_budget, seconds):
    target, pairs, initial, quads, rows, supports = reconstruct(hub)
    start = time.monotonic()
    trace = []
    solutions = set()
    solution_visits = 0

    def apply(demands, available, chosen):
        result = demands.copy()
        for rid in chosen:
            if not available & (1 << rid):
                return None
            available &= ~(1 << rid)
            for p in rows[rid]:
                result[p] -= 1
                if result[p] == 0:
                    available &= ~supports[p]
                elif result[p] < 0:
                    return None
        return result, available

    def visit(demands, available, selected):
        nonlocal solution_visits
        if len(trace) >= node_budget or time.monotonic() - start >= seconds:
            return None, False
        node_id = len(trace)
        node = {"id": node_id, "selected_rows": sorted(selected),
                "demands_hex": hex(sum(n << (2 * p) for p, n in enumerate(demands)))}
        trace.append(node)
        positive = [p for p, n in enumerate(demands) if n]
        if not positive:
            require(len(selected) == 13, "wrong solution row count")
            solution = tuple(sorted(selected))
            link = list(map(tuple, hub)) + [quads[r] for r in solution]
            require(len(link) == len(set(link)) == 19, "duplicate link solution")
            counts = Counter(p for b in link for p in itertools.combinations(b, 2))
            require(dict(counts) == target, "wrong link pair multiplicities")
            solutions.add(solution)
            solution_visits += 1
            node["status"] = "SOLUTION"
            return node_id, True
        carriers = {p: available & supports[p] for p in positive}
        deficient = [p for p in positive if carriers[p].bit_count() < demands[p]]
        if deficient:
            p = min(deficient)
            node.update({"status": "DEFICIENT_PAIR", "pair_id": p,
                         "carriers": list(bits(carriers[p]))})
            return node_id, True
        forced = [p for p in positive if carriers[p].bit_count() == demands[p]]
        if forced:
            p = min(forced, key=lambda p: (demands[p], p))
            chosen = tuple(bits(carriers[p]))
            node.update({"pair_id": p, "forced_rows": list(chosen)})
            next_state = apply(demands, available, chosen)
            if next_state is None:
                node["status"] = "FORCED_CONFLICT"
                return node_id, True
            child_id, complete = visit(*next_state, selected + chosen)
            node.update({"status": "FORCED" if complete else "UNKNOWN",
                         "child": child_id})
            return node_id, complete
        p = min(positive, key=lambda p: (carriers[p].bit_count(), -demands[p], p))
        options = tuple(bits(carriers[p]))
        node.update({"pair_id": p, "branches": list(options), "children": []})
        for rid in options:
            next_state = apply(demands, available, (rid,))
            require(next_state is not None, "invalid eligible row")
            child_id, complete = visit(*next_state, selected + (rid,))
            node["children"].append(child_id)
            if not complete:
                node["status"] = "UNKNOWN"
                return node_id, False
        node["status"] = "EXHAUSTED"
        return node_id, True

    _, complete = visit(initial, (1 << len(rows)) - 1, ())
    links = [sorted(list(map(tuple, hub)) + [quads[r] for r in solution])
             for solution in sorted(solutions)]
    return {"status": "COMPLETE" if complete else "UNKNOWN",
            "seconds": time.monotonic() - start, "nodes": len(trace),
            "candidate_count": len(rows), "pairs": pairs, "initial_demands": initial,
            "quad_candidates": quads, "unique_solutions": len(solutions),
            "solution_visits": solution_visits, "solution_row_ids": sorted(solutions),
            "links": sorted(links), "links_sha256": digest(sorted(links)),
            "trace": trace, "trace_sha256": digest(trace)}


def save(path, title, body):
    header = {"Document": title, "Version": "v1.0.0", "Author": "Celaya Solutions",
              "Contact": "hello@celayasolutions.com", "Date": "2026-10-03",
              "SHA256": digest(body), "Chain": "n/a", "Tx": "[not anchored]",
              "License": "All Rights Reserved / Celaya Solutions"}
    path.write_bytes(gzip.compress(raw_json({"document_header": header, "body": body})
                                   + b"\n", mtime=0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seconds", type=float, default=5.0)
    parser.add_argument("--nodes", type=int, default=250_000)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    require(args.seconds > 0 and args.nodes > 0 and args.limit >= 0, "positive budgets")
    require(not args.output.exists(), "refusing to overwrite output")
    args.output.mkdir(parents=True)
    raw = (args.directory / "metadata.json").read_bytes()
    metadata = json.loads(raw)
    summaries = []
    for index, shape in enumerate(metadata["shapes"][:args.limit or None]):
        result = enumerate_hub(shape["hub_blocks"], args.nodes, args.seconds)
        result.update({"shape_index": index, "hub_blocks": shape["hub_blocks"],
                       "shape_sha256": digest(shape)})
        path = args.output / f"case-{index:03}.json.gz"
        save(path, f"Independent Link Decomposition Tree for Hub Shape {index}", result)
        summary = {k: result[k] for k in ["shape_index", "status", "seconds", "nodes",
                   "unique_solutions", "solution_visits", "candidate_count", "links_sha256"]}
        summary.update({"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        summaries.append(summary)
        print(json.dumps(summary), flush=True)
    body = {"scope": "Only cases marked COMPLETE are exhaustive; normalized degree19 links",
            "input_metadata_sha256": hashlib.sha256(raw).hexdigest(),
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                        text=True).strip(),
            "python_version": platform.python_version(), "seed": None,
            "per_case_node_budget": args.nodes, "per_case_seconds_budget": args.seconds,
            "results": summaries}
    save(args.output / "manifest.json.gz", "Independent Link Decomposition Enumeration", body)
    print(json.dumps({"cases": len(summaries), "complete": sum(
        r["status"] == "COMPLETE" for r in summaries),
        "solutions": sum(r["unique_solutions"] for r in summaries),
        "nodes": sum(r["nodes"] for r in summaries)}), flush=True)


if __name__ == "__main__":
    main()
