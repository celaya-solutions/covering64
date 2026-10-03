#!/usr/bin/env python3
# Document:    Independent Replay of Complete Link Hub Decomposition Trees
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      0e7bceb1d9a413dee5768b724f755841eb98bea6dde7fe0618444e4be8cc23ac
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay complete residual-decomposition trees with dictionaries and sets.

Imports neither the enumerator, the shape auditor, nor the CP hub builder.
Rebuilds every state directly from its selected quadruples and all universe
rows. Checks branch exhaustiveness, forced rows, and every solution leaf.
"""

import argparse
import gzip
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def read(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def replay(case, hub):
    body = case["body"]
    require(case["document_header"]["SHA256"] == digest(body), "case body hash")
    require(body["status"] == "COMPLETE", "incomplete tree")
    require(body["hub_blocks"] == hub, "hub identity")
    require(len(hub) == len(set(map(tuple, hub))) == 6, "hub count or duplicates")
    require(all(len(b) == 4 and b == sorted(set(b)) and 2 in b and
                all(type(x) is int and 2 <= x <= 16 for x in b) for b in hub),
            "malformed hub")
    target = Counter({p: 1 for p in itertools.combinations(range(2, 17), 2)})
    target.update((2, x) for x in range(3, 7))
    target.update((x, x + 1) for x in range(7, 17, 2))
    initial = dict(target)
    for block in hub:
        for pair in itertools.combinations(block, 2):
            initial[pair] -= 1
    require(all(n >= 0 for n in initial.values()), "hub overuses pair")
    require(all(n == 0 for p, n in initial.items() if 2 in p), "hub not exhausted")
    pairs = list(itertools.combinations(range(3, 17), 2))
    require(body["pairs"] == [list(p) for p in pairs], "pair universe")
    require(body["initial_demands"] == [initial[p] for p in pairs], "initial demands")
    quads = [q for q in itertools.combinations(range(3, 17), 4)
             if all(initial[p] > 0 for p in itertools.combinations(q, 2))]
    require(body["quad_candidates"] == [list(q) for q in quads], "candidate completeness")
    require(body["candidate_count"] == len(quads), "candidate count")
    incidence = [set(itertools.combinations(q, 2)) for q in quads]
    nodes = body["trace"]
    require(len(nodes) == body["nodes"] and nodes, "trace node count")
    require(body["trace_sha256"] == digest(nodes), "trace hash")
    seen = set()
    solutions = set()
    solution_visits = 0

    def remaining(selected):
        demands = {p: initial[p] for p in pairs}
        for row in selected:
            for pair in incidence[row]:
                demands[pair] -= 1
        return demands

    def visit(nid, selected):
        nonlocal solution_visits
        require(type(nid) is int and 0 <= nid < len(nodes), "bad child ID")
        require(nid not in seen, "cycle or reused tree node")
        seen.add(nid)
        node = nodes[nid]
        require(node["id"] == nid, "node identity")
        require(len(selected) == len(set(selected)), "duplicate selected row")
        require(all(type(r) is int and 0 <= r < len(quads) for r in selected), "row ID")
        require(node["selected_rows"] == sorted(selected), "selected path")
        demands = remaining(selected)
        require(min(demands.values()) >= 0, "negative demand on path")
        packed = sum(demands[p] * 4 ** i for i, p in enumerate(pairs))
        require(node["demands_hex"] == hex(packed), "state demand mismatch")
        if node["status"] == "SOLUTION":
            require(all(n == 0 for n in demands.values()), "incomplete solution")
            require(len(selected) == 13, "solution row count")
            link = list(map(tuple, hub)) + [quads[r] for r in selected]
            require(len(set(link)) == 19, "duplicate link block")
            actual = Counter(p for q in link for p in itertools.combinations(q, 2))
            require(actual == target, "wrong solution pair incidence")
            solutions.add(tuple(sorted(selected)))
            solution_visits += 1
            return
        require(any(n > 0 for n in demands.values()), "non-solution leaf with zero demand")
        pid = node["pair_id"]
        require(type(pid) is int and 0 <= pid < len(pairs), "pair ID")
        p = pairs[pid]
        require(demands[p] > 0, "branch pair is satisfied")
        carriers = [rid for rid, row in enumerate(incidence)
                    if rid not in selected and p in row and all(demands[q] > 0 for q in row)]
        status = node["status"]
        if status == "DEFICIENT_PAIR":
            require(node["carriers"] == carriers, "deficient carriers mismatch")
            require(len(carriers) < demands[p], "false deficient-pair leaf")
        elif status in ["FORCED", "FORCED_CONFLICT"]:
            require(node["forced_rows"] == carriers, "omitted forced carrier")
            require(len(carriers) == demands[p], "unjustified forced rows")
            new = selected + carriers
            new_demands = remaining(new)
            feasible = all(n >= 0 for n in new_demands.values())
            if status == "FORCED_CONFLICT":
                require(not feasible, "false forced conflict")
            else:
                require(feasible, "infeasible forced path")
                visit(node["child"], new)
        elif status == "EXHAUSTED":
            require(node["branches"] == carriers, "omitted or extra branch")
            require(len(carriers) >= demands[p], "branch should have been deficient")
            require(len(node["children"]) == len(carriers), "omitted child")
            for row, child in zip(carriers, node["children"]):
                visit(child, selected + [row])
        else:
            raise ValueError("unknown or incomplete node status")

    visit(0, [])
    require(seen == set(range(len(nodes))), "unreachable tree node")
    require(body["unique_solutions"] == len(solutions), "unique solution count")
    require(body["solution_visits"] == solution_visits, "solution visits")
    require(body["solution_row_ids"] == [list(s) for s in sorted(solutions)],
            "solution row list")
    links = sorted(sorted(list(map(tuple, hub)) + [quads[r] for r in s]) for s in solutions)
    require(body["links"] == [[list(b) for b in link] for link in links], "solution link list")
    require(body["links_sha256"] == digest(links), "solution hash")
    return {"nodes": len(nodes), "unique_solutions": len(solutions),
            "solution_visits": solution_visits, "links_sha256": digest(links)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    metadata_raw = args.metadata.read_bytes()
    metadata = json.loads(metadata_raw)
    manifest = read(args.directory / "manifest.json.gz")
    body = manifest["body"]
    require(manifest["document_header"]["SHA256"] == digest(body), "manifest hash")
    require(body["input_metadata_sha256"] == hashlib.sha256(metadata_raw).hexdigest(),
            "input metadata hash")
    require(len(body["results"]) == len(metadata["shapes"]), "missing manifest case")
    results = []
    for index, (shape, summary) in enumerate(zip(metadata["shapes"], body["results"])):
        require(summary["shape_index"] == index, "manifest index")
        path = args.directory / summary["file"]
        require(hashlib.sha256(path.read_bytes()).hexdigest() == summary["sha256"],
                "case byte hash")
        case = read(path)
        require(case["body"]["shape_index"] == index, "case index")
        require(case["body"]["shape_sha256"] == digest(shape), "shape hash")
        result = replay(case, shape["hub_blocks"])
        require(result["nodes"] == summary["nodes"], "manifest node count")
        require(result["unique_solutions"] == summary["unique_solutions"], "manifest solutions")
        results.append(result)
    print(json.dumps({"status": "VERIFIED_COMPLETE", "cases": len(results),
                      "nodes": sum(r["nodes"] for r in results),
                      "solutions": sum(r["unique_solutions"] for r in results),
                      "checker_source_sha256": hashlib.sha256(
                          Path(__file__).read_bytes()).hexdigest(),
                      "manifest_sha256": hashlib.sha256(
                          (args.directory / "manifest.json.gz").read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
