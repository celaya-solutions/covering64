#!/usr/bin/env python3
# Document:    Exact Larger Heavy Link Neighborhood Enumeration
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Count proper three-edge and paired two-anchor switches without optimization."""

import itertools as it
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

from basis import digest, rebuild
from bundle_check import BUNDLE, incumbent_upper, rational, sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/lp-guided-larger-moves-20261004"


def main():
    output = HERE / "larger-moves.json"
    assert not output.exists() and not RAW.exists()
    audit = json.loads((HERE / "bundle-audit.json").read_text())
    assert audit["passed"] and audit["bundle_sha256"] == sha(BUNDLE)
    bundle = json.loads(BUNDLE.read_text())
    proposal_path = HERE.parent / "lp-guided-full-sweep/proposal.json"
    proposal = json.loads(proposal_path.read_text())
    blocks, anchors, _, heavy, rows = rebuild()
    chosen = frozenset(blocks[i] for i in proposal["baseline_heavy_global_ids"])
    allowed = set(heavy)
    heavy_index = {block: i for i, block in enumerate(heavy)}
    upper, upper_evidence = incumbent_upper(rows, heavy, chosen)
    baseline_counts = Counter(t for block in chosen for t in it.combinations(block, 3))

    def passes_cap(removed, added):
        delta = Counter(t for block in added for t in it.combinations(block, 3))
        delta.subtract(t for block in removed for t in it.combinations(block, 3))
        return all(baseline_counts[t] + count <= 2 or frozenset(t) in anchors
                   for t, count in delta.items())

    def local_moves(anchor, size):
        local = sorted(block for block in chosen if anchor <= set(block))
        moves, raw = [], 0
        for outgoing in it.combinations(local, size):
            degree = Counter(p for block in outgoing for p in set(block) - anchor)
            edges = list(it.combinations(sorted(degree), 2))
            for incoming_edges in it.combinations(edges, size):
                if Counter(p for edge in incoming_edges for p in edge) != degree:
                    continue
                incoming = frozenset(tuple(sorted(anchor | set(edge))) for edge in incoming_edges)
                if len(incoming - chosen) != size:
                    continue
                raw += 1
                if incoming <= allowed:
                    moves.append((frozenset(outgoing), incoming))
        assert len(moves) == len(set(moves))
        return raw, moves

    baseline_positions = [heavy_index[block] for block in chosen]
    planes = [(cut["rhs"] - sum(cut["coefficients"][i] for i in baseline_positions),
               cut["coefficients"]) for cut in bundle["cuts"]]
    assert all(cut["denominator"] == 1000000 for cut in bundle["cuts"])

    def exact_numerator(removed, added):
        outgoing = [heavy_index[block] for block in removed]
        incoming = [heavy_index[block] for block in added]
        return max(0, *(baseline + sum(coefficients[i] for i in outgoing)
                        - sum(coefficients[i] for i in incoming)
                        for baseline, coefficients in planes))

    def summarize(moves):
        records, states = [], set()
        for removed, added, metadata in moves:
            state = chosen - removed | added
            assert len(state) == 28 and state <= allowed
            key = tuple(sorted(heavy_index[block] for block in state))
            assert key not in states
            states.add(key)
            numerator = exact_numerator(removed, added)
            records.append({"removed_heavy_ids": sorted(heavy_index[block] for block in removed),
                            "added_heavy_ids": sorted(heavy_index[block] for block in added),
                            "state_sha256": digest(sorted(state)),
                            "lower_bound_numerator": numerator, **metadata})
        numerators = [r["lower_bound_numerator"] for r in records]
        summary = {
            "valid_unique_states": len(records),
            "states_sha256": digest(sorted(states)),
            "positive_exact_lower_bound": sum(n > 0 for n in numerators),
            "pruned_against_exact_incumbent_upper": sum(Fraction(n, 1000000) >= upper
                                                        for n in numerators),
            "minimum_lower_bound": rational(Fraction(min(numerators), 1000000)),
            "maximum_lower_bound": rational(Fraction(max(numerators), 1000000)),
        }
        return summary, records

    triples, twos, triple_counts, two_counts = [], [], [], []
    for i, anchor in enumerate(anchors):
        raw_three, local_three = local_moves(anchor, 3)
        assert raw_three == 245
        legal_three = [(removed, added, {"anchor_index": i}) for removed, added in local_three
                       if passes_cap(removed, added)]
        triples.extend(legal_three)
        triple_counts.append({"anchor": sorted(anchor), "raw": raw_three,
                              "within_heavy_universe": len(local_three),
                              "passes_global_triple_cap": len(legal_three)})
        raw_two, local_two = local_moves(anchor, 2)
        assert raw_two == 40
        twos.append(local_two)
        two_counts.append({"anchor": sorted(anchor), "raw": raw_two,
                           "within_heavy_universe": len(local_two),
                           "passes_global_triple_cap": sum(passes_cap(*move)
                                                           for move in local_two)})
    assert sum(row["passes_global_triple_cap"] for row in two_counts) == 136
    paired, pair_counts = [], []
    for a, b in it.combinations(range(4), 2):
        accepted, cancellation = 0, 0
        for (removed_a, added_a), (removed_b, added_b) in it.product(twos[a], twos[b]):
            assert not (removed_a & removed_b) and not (added_a & added_b)
            removed, added = removed_a | removed_b, added_a | added_b
            if not passes_cap(removed, added):
                continue
            accepted += 1
            failing_constituents = sum(not passes_cap(*move) for move in
                                       ((removed_a, added_a), (removed_b, added_b)))
            cancellation += failing_constituents > 0
            paired.append((removed, added, {"anchor_indices": [a, b],
                                           "individually_cap_failing": failing_constituents}))
        pair_counts.append({"anchor_indices": [a, b], "raw": 1600,
                            "within_heavy_universe": len(twos[a]) * len(twos[b]),
                            "passes_joint_triple_cap": accepted,
                            "jointly_valid_but_individually_invalid": cancellation})
    triple_summary, triple_records = summarize(triples)
    pair_summary, pair_records = summarize(paired)
    triple_summary["per_anchor"] = triple_counts
    pair_summary["constituent_two_edge_counts"] = two_counts
    pair_summary["per_anchor_pair"] = pair_counts
    pair_summary["jointly_valid_but_individually_invalid"] = sum(
        row["jointly_valid_but_individually_invalid"] for row in pair_counts)
    RAW.mkdir()
    for name, records in (("proper-three", triple_records), ("paired-two", pair_records)):
        (RAW / f"{name}.json").write_text(json.dumps(records, indent=2) + "\n")
    report = {
        "passed": True, "solver_calls": 0, "checker_sha256": sha(__file__),
        "basis_source_sha256": sha(HERE / "basis.py"),
        "bundle_checker_sha256": sha(HERE / "bundle_check.py"),
        "bundle_audit_sha256": sha(HERE / "bundle-audit.json"),
        "bundle_sha256": sha(BUNDLE), "proposal_sha256": sha(proposal_path),
        "baseline_heavy_global_ids": proposal["baseline_heavy_global_ids"],
        "incumbent_upper": upper_evidence, "envelope_planes": 113,
        "proper_three_edge": triple_summary, "paired_two_anchor": pair_summary,
        "raw_sha256": {str(p.relative_to(ROOT)): sha(p) for p in sorted(RAW.iterdir())},
        "scope": "Finite degree-preserving neighborhoods of the fixed best heavy tuple.",
        "global_lower_bound_claim": False,
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
