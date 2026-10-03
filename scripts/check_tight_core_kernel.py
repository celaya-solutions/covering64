#!/usr/bin/env python3
# Document:    Standalone tight core kernel enumeration
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Independently reconstruct and exhaust the selected 55-core-block completion."""

import argparse
import gzip
import hashlib
import json
from itertools import combinations
from pathlib import Path


def run(source, output):
    raw = source.read_bytes()
    candidate = json.loads(gzip.decompress(raw))["candidates"][0]
    blocks = list(combinations(range(1, 17), 5))
    triples = list(combinations(range(1, 17), 3))
    ids = {t: i for i, t in enumerate(triples)}
    coverage = [{ids[t] for t in combinations(b, 3)} for b in blocks]
    retained = [tuple(b) for b in candidate["retained_core_blocks"]]
    if (len(retained) != 55 or len(set(retained)) != 55
            or any(type(p) is not int for b in retained for p in b)
            or any(b not in blocks for b in retained)):
        raise ValueError("Invalid retained block set")
    covered = {ids[t] for b in retained for t in combinations(b, 3)}
    missing = set(range(560)) - covered
    denominator = candidate["denominator"]
    if type(denominator) is not int or denominator <= 0:
        raise ValueError("Invalid denominator")
    if any(type(t) is not int or type(n) is not int or n <= 0
           for t, n in candidate["weights"]):
        raise ValueError("Invalid integer weight entry")
    weights = {t: (5*n + denominator//2)//denominator for t, n in candidate["weights"]}
    if len(weights) != len(candidate["weights"]) or not all(0 <= t < 560 and w > 0
                                                          for t, w in weights.items()):
        raise ValueError("Malformed dual weights")
    if set(weights) & covered or sum(weights.values()) != 45:
        raise ValueError("Dual is not a nine-block lower bound on this residual")
    loads = [sum(weights.get(t, 0) for t in row) for row in coverage]
    if max(loads) > 5:
        raise ValueError("Reconstructed rational dual is infeasible")
    tight = [i for i, load in enumerate(loads) if load == 5]
    positive = set(weights)
    positive_masks = [sum(1 << t for t in coverage[i] & positive) for i in tight]
    cover_masks = [sum(1 << t for t in coverage[i] & missing) for i in tight]
    compatible = [sum(1 << j for j, other in enumerate(positive_masks) if not mask & other)
                  for mask in positive_masks]
    containing = {t: sum(1 << j for j, i in enumerate(tight) if t in coverage[i]) for t in missing}
    goal = sum(1 << t for t in missing)
    nodes = []
    witness = None

    def visit(available, covered_mask, chosen):
        nonlocal witness
        index = len(nodes)
        node = {"chosen_block_ids": [tight[i] for i in chosen]}
        nodes.append(node)
        need = goal & ~covered_mask
        if not need:
            witness = sorted(retained + [blocks[tight[i]] for i in chosen])
            node["cover_found"] = True
            return index
        options, triple = min(((available & containing[t], t) for t in missing if need >> t & 1),
                              key=lambda item: (item[0].bit_count(), item[1]))
        node.update(required_triple=list(triples[triple]),
                    candidate_block_ids=[tight[i] for i in range(len(tight)) if options >> i & 1],
                    children=[])
        while options and witness is None:
            bit = options & -options
            i = bit.bit_length() - 1
            options ^= bit
            child = visit(available & compatible[i], covered_mask | cover_masks[i], chosen + [i])
            node["children"].append(child)
        return index

    visit((1 << len(tight)) - 1, 0, [])
    result = {"scope": "only the listed retained 55-block core neighborhood",
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "input_sha256": hashlib.sha256(raw).hexdigest(),
              "retained_blocks": retained, "missing_triples": [triples[t] for t in sorted(missing)],
              "dual_denominator": 5, "dual_weights": sorted(weights.items()),
              "dual_bound": 9, "tight_block_ids": tight, "tight_blocks": [blocks[i] for i in tight],
              "nodes": nodes, "node_count": len(nodes), "witness": witness,
              "exhausted_without_cover": witness is None}
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("scope", "dual_bound", "node_count",
                                            "exhausted_without_cover")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run(args.source, args.output)
