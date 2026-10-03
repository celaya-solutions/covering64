#!/usr/bin/env python3
# Document:    Standalone Fraction and Set Replay of Weighted Kernel Search Trees
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      030f9785842942e8b45df65328528f71069fe59e70d05b64263f711d88b69179
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check complete local no-completion trees without importing their producer.

This checker uses Fraction and sets of triples. It independently rebuilds the
full universe, retained coverage, all capacities, the reduction, and every
tree state. A branch is complete only when it lists every admissible block
covering its chosen uncovered triple. No CP/SAT solver or package is used.
"""

import argparse
import gzip
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path


def check(ok, message):
    if not ok:
        raise ValueError(message)


def sha(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = path.read_bytes()
    return raw, json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def verify(data, certificate, input_sha):
    body = certificate["body"]
    check(certificate["document_header"]["SHA256"] == sha(body), "body hash")
    check(body["input_sha256"] == input_sha, "input byte hash")
    check(body["input_json_sha256"] == sha(data), "input JSON hash")
    m = data["additional_blocks_allowed"]
    check(type(m) is int and m > 0, "bad block budget")
    check(body["additional_blocks_allowed"] == m, "certificate block budget")
    triples = list(itertools.combinations(range(1, 17), 3))
    blocks = list(itertools.combinations(range(1, 17), 5))
    triple_rank = {t: i for i, t in enumerate(triples)}
    covers = [set(itertools.combinations(block, 3)) for block in blocks]
    all_triples = set(triples)
    check(body["universe_block_count"] == 4368, "block universe count")
    check(body["universe_triple_count"] == 560, "triple universe count")
    check(body["universe_blocks_sha256"] == sha(blocks), "blocks hash")
    check(body["universe_triples_sha256"] == sha(triples), "triples hash")
    results = body["results"]
    check(len(results) == len(data["candidates"]), "missing case")
    total_nodes = 0
    for index, (case, result) in enumerate(zip(data["candidates"], results)):
        check(result["case_index"] == index, "wrong case index")
        check(result["input_case_sha256"] == sha(case), "case hash")
        check(result["removed_core_positions"] == case["removed"], "case identity")
        check(result["status"] == "EXHAUSTED", "not a complete negative tree")
        check(result["witness"] is None, "negative certificate has witness")
        retained = case["retained_block_ids"]
        check(all(type(b) is int and 0 <= b < len(blocks) for b in retained),
              "bad retained ID")
        check(retained == sorted(set(retained)), "duplicate or unordered retained IDs")
        check([list(blocks[b]) for b in retained] == case["retained_core_blocks"],
              "retained blocks mismatch")
        check(len(retained) + m == 64, "wrong neighborhood size")
        retained_set = set(retained)
        missing = all_triples.difference(set().union(*(covers[b] for b in retained)))
        d = case["denominator"]
        check(type(d) is int and d > 0, "bad denominator")
        weight = {}
        for pair in case["weights"]:
            check(isinstance(pair, list) and len(pair) == 2, "bad weight pair")
            tid, numerator = pair
            check(type(tid) is int and 0 <= tid < len(triples), "bad triple ID")
            check(type(numerator) is int and numerator > 0, "bad weight")
            t = triples[tid]
            check(t not in weight and t in missing, "duplicate or covered weight")
            weight[t] = Fraction(numerator, d)
        bound = sum(weight.values(), Fraction())
        check(m - 1 < bound <= m, "unsupported bound")
        check(case["exact_lower_bound"] == [bound.numerator, bound.denominator],
              "input bound mismatch")
        capacities = [sum((weight.get(t, Fraction()) for t in ts), Fraction())
                      for ts in covers]
        check(all(cap <= 1 for cap in capacities), "dual infeasible")
        cutoff = bound - (m - 1)
        pool = [b for b, cap in enumerate(capacities) if cap >= cutoff]
        check(pool == case["allowed_block_ids"], "pool completeness")
        check([list(blocks[b]) for b in pool] == case["allowed_blocks"], "pool blocks")
        check(len(pool) == case["allowed_block_count"], "input pool count")
        check(Fraction(case["minimum_block_load_numerator"], d) == cutoff,
              "input cutoff")
        integer_caps = [int(cap * d) for cap in capacities]
        check(result["all_4368_capacity_numerators"] == integer_caps,
              "saved capacities mismatch")
        check(result["capacities_sha256"] == sha(integer_caps), "capacities hash")
        check(result["pool_count"] == len(pool), "result pool count")
        check(result["residual_triple_count"] == len(missing), "residual count")
        check(result["dual_bound"] == case["exact_lower_bound"], "result bound")
        check(result["denominator"] == d, "result denominator")
        check(Fraction(result["slack_numerator"], d) == m - bound, "result slack")
        check(Fraction(result["cutoff_numerator"], d) == cutoff, "result cutoff")
        nodes = result["trace"]
        check(result["node_count"] == len(nodes) and nodes, "node count")
        check(result["trace_sha256"] == sha(nodes), "trace hash")
        seen = set()

        def replay(node_id, selected):
            check(type(node_id) is int and 0 <= node_id < len(nodes), "invalid node ID")
            check(node_id not in seen, "cycle or shared tree node")
            seen.add(node_id)
            node = nodes[node_id]
            check(node["id"] == node_id, "node identity")
            check(node["selected_block_ids"] == selected, "path mismatch")
            check(len(selected) == len(set(selected)), "duplicate selected block")
            check(not retained_set.intersection(selected), "retained selected twice")
            check(all(b in pool for b in selected), "selected block outside pool")
            covered = set().union(*(covers[b] for b in selected)) if selected else set()
            uncovered = missing.difference(covered)
            union_weight = sum((w for t, w in weight.items() if t in covered), Fraction())
            loss = len(selected) - union_weight
            check(loss <= m - bound, "ineligible path")
            check(Fraction(node["covered_weight_numerator"], d) == union_weight,
                  "covered weight mismatch")
            check(Fraction(node["loss_numerator"], d) == loss, "loss mismatch")
            mask = sum(2 ** triple_rank[t] for t in uncovered)
            check(node["uncovered_mask_hex"] == hex(mask), "uncovered mismatch")
            check(uncovered, "negative tree contains a cover")
            if len(selected) == m:
                check(node["status"] == "EXHAUSTED_DEPTH", "wrong depth leaf")
                check(not node.get("children"), "depth leaf has children")
                return
            check(len(selected) < m, "path too long")
            tid = node["branch_triple_id"]
            check(type(tid) is int and 0 <= tid < len(triples), "bad branch triple")
            branch = triples[tid]
            check(branch in uncovered, "branch triple is already covered")
            options = []
            for bid in pool:
                if bid in selected or branch not in covers[bid]:
                    continue
                new_weight = sum((weight.get(t, Fraction())
                                  for t in covers[bid].intersection(uncovered)), Fraction())
                if loss + 1 - new_weight <= m - bound:
                    options.append(bid)
            check(node["eligible_block_ids"] == options, "omitted or extra branch")
            if not options:
                check(node["status"] == "EXHAUSTED_NO_ELIGIBLE_BLOCK", "bad dead leaf")
                check(not node.get("children"), "dead leaf has children")
                return
            check(node["status"] == "EXHAUSTED", "internal node not exhausted")
            children = node["children"]
            check(len(children) == len(options), "omitted child")
            for bid, child in zip(options, children):
                check(child["block_id"] == bid and child["status"] == "EXHAUSTED",
                      "bad child edge")
                replay(child["node_id"], selected + [bid])

        replay(0, [])
        check(seen == set(range(len(nodes))), "unreachable certificate node")
        total_nodes += len(nodes)
    return {"status": "VERIFIED_LOCAL_NO_COMPLETION", "cases": len(results),
            "nodes": total_nodes, "scope": body["scope"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("certificate", type=Path)
    args = parser.parse_args()
    raw, data = read(args.input)
    _, certificate = read(args.certificate)
    result = verify(data, certificate, hashlib.sha256(raw).hexdigest())
    result["checker_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result["certificate_sha256"] = hashlib.sha256(args.certificate.read_bytes()).hexdigest()
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
