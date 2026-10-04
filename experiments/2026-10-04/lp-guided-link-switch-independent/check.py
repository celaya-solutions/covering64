# Document:    Independent Gate for Degree-Preserving LP-Guided Link Switches
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      b46c7b43c9247e021ac68174b85600b497588acfeda3107211fe6d4c861609d6
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import importlib.util
import itertools as it
import json
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "lp-guided-link-switch/prepare.py"
PROPOSAL = HERE.parent / "lp-guided-link-switch/proposal.json"
INF = 2**63 - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def main():
    assert sha(SOURCE) == "cd42848df3e6faaa19b510062fc97a8c7ac323193875e0809fbccdfa8b4dbd68"
    assert sha(PROPOSAL) == "46839a033b76abf0d2cca0974f67e021e80b975d6f7861664ed0e0b6f80624b0"
    proposal = json.loads(PROPOSAL.read_text())
    for path, expected in proposal["input_files"].items():
        assert sha(ROOT / path) == expected
    universe = list(it.combinations(range(1, 17), 5))
    global_ids = {b: i for i, b in enumerate(universe)}
    anchors = [frozenset(range(a, a + 3)) for a in (1, 5, 9, 13)]
    ordinary = [b for b in universe if all(len(set(b) & a) <= 1 for a in anchors)]
    heavy = [
        b
        for b in universe
        if sum(a <= set(b) for a in anchors) == 1
        and all(len(set(b) & a) in (0, 1, 3) for a in anchors)
    ]
    assert len(ordinary) == 1200 and len(heavy) == 276
    heavy_set = set(heavy)
    local_ids = {b: i for i, b in enumerate(heavy)}
    seed_path = ROOT / (
        "experiments/2026-10-03/four-seven-template-native-lookahead/performance-cycle-best.txt"
    )
    family = [tuple(map(int, line.split())) for line in seed_path.read_text().splitlines()]
    fixed = set(family) & heavy_set
    assert len(family) == len(set(family)) == 64 and len(fixed) == 28
    assert proposal["initial_heavy_global_ids"] == [global_ids[b] for b in sorted(fixed)]
    assert proposal["ordinary_global_ids"] == [global_ids[b] for b in ordinary]

    def profile(chosen):
        assert len(chosen) == 28 and set(chosen) <= heavy_set
        for anchor in anchors:
            blocks = [b for b in chosen if anchor <= set(b)]
            outside = Counter(p for b in blocks for p in set(b) - anchor)
            assert len(blocks) == 7 and outside == {
                p: 2 if p == max(anchor) + 1 else 1 for p in range(1, 17) if p not in anchor
            }
        counts = Counter(t for b in chosen for t in it.combinations(b, 3))
        assert all(n <= 2 or frozenset(t) in anchors for t, n in counts.items())

    profile(fixed)
    # Exhaust every two-edge replacement on the endpoint multiset, rather than
    # using the generator's two named reconnection formulas.
    neighbors = {}
    for anchor in anchors:
        local = [b for b in sorted(fixed) if anchor <= set(b)]
        for removed in it.combinations(local, 2):
            old_edges = [tuple(sorted(set(b) - anchor)) for b in removed]
            degrees = Counter(p for edge in old_edges for p in edge)
            endpoints = sorted(degrees)
            possible_edges = list(it.combinations(endpoints, 2))
            for replacement in it.combinations(possible_edges, 2):
                if Counter(p for edge in replacement for p in edge) != degrees:
                    continue
                added = {tuple(sorted(set(edge) | anchor)) for edge in replacement}
                if added == set(removed):
                    continue
                chosen = (fixed - set(removed)) | added
                if len(chosen) != 28 or not chosen <= heavy_set:
                    continue
                counts = Counter(t for b in chosen for t in it.combinations(b, 3))
                if any(n > 2 and frozenset(t) not in anchors for t, n in counts.items()):
                    continue
                profile(chosen)
                neighbors[tuple(sorted(chosen))] = {
                    "anchor": sorted(anchor),
                    "removed": [list(b) for b in sorted(removed)],
                    "added": [list(b) for b in sorted(added)],
                }
    assert len(neighbors) == len(proposal["candidates"]) == 132
    # Rebuild every row directly from its support, including the finite upper
    # bounds, then compare the generator's affine shifts on all 132 neighbors.
    pairs = list(it.combinations(range(1, 17), 2))
    pair_bounds = {}
    for p, q in pairs:
        containing = [a for a in anchors if p in a or q in a]
        if not containing:
            pair_bounds[p, q] = (5, 7)
        elif any(p in a and q in a for a in anchors):
            pair_bounds[p, q] = (7, 7)
        elif any((p in a and q == max(a) + 1) or (q in a and p == max(a) + 1) for a in anchors):
            pair_bounds[p, q] = (6, 6)
        else:
            pair_bounds[p, q] = (5, 5)
    supports = [((), 64, 64)]
    supports += [
        (t, 1, INF if frozenset(t) in anchors else 2) for t in it.combinations(range(1, 17), 3)
    ]
    supports += [((p,), 20, 20) for p in range(1, 17)]
    supports += [(pair, *pair_bounds[pair]) for pair in pairs]
    symbolic = []
    for support, lower, upper in supports:
        os = [i for i, b in enumerate(ordinary) if set(support) <= set(b)]
        hs = [i for i, b in enumerate(heavy) if set(support) <= set(b)]
        symbolic.append((os, hs, lower, upper))
    assert len(symbolic) == 697

    def concrete(chosen):
        values = []
        for (support, lower, upper), (os, _, _, _) in zip(supports, symbolic, strict=True):
            count = sum(set(support) <= set(b) for b in chosen)
            values.append(
                (os, [1] * len(os), lower - count, upper if upper == INF else upper - count)
            )
        return values

    spec = importlib.util.spec_from_file_location("reviewed_generator", SOURCE)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    initial = concrete(fixed)
    assert initial == generator.shifted_rows(symbolic, heavy, fixed)
    assert digest(initial) == proposal["initial_shifted_rows_sha256"]
    base_manifest = json.loads(
        (ROOT / "experiments/2026-10-03/lookahead-heavy-strengthened/manifest.json").read_text()
    )
    proto = text_format.Parse(
        (ROOT / base_manifest["model"]).read_text(), cp_model_pb2.CpModelProto()
    )
    actual = [
        (list(c.linear.vars), list(c.linear.coeffs), *c.linear.domain) for c in proto.constraints
    ]
    assert initial == actual
    bundle_path = ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/cut-bundle.json"
    bundle = json.loads(bundle_path.read_text())
    cuts = bundle["cuts"]
    assert len(cuts) == 14 and bundle["heavy_global_ids"] == [global_ids[b] for b in heavy]
    assert bundle["ordinary_global_ids"] == [global_ids[b] for b in ordinary]
    dual_weight_bounds = []
    for cut in cuts:
        dual_path = ROOT / cut["dual_path"]
        assert sha(dual_path) == cut["dual_sha256"]
        dual = json.loads(dual_path.read_text())
        assert dual["denominator"] == cut["denominator"] == 1000
        bound = max(abs(w) for _, w in dual["weights"])
        assert bound <= 1000
        dual_weight_bounds.append(bound)
    expected_records = []
    for chosen, move in neighbors.items():
        rows = concrete(chosen)
        assert rows == generator.shifted_rows(symbolic, heavy, chosen)
        ids = [local_ids[b] for b in chosen]
        violations = [max(0, c["rhs"] - sum(c["coefficients"][i] for i in ids)) for c in cuts]
        expected_records.append(
            {
                **move,
                "heavy_global_ids": [global_ids[b] for b in chosen],
                "heavy_local_ids": ids,
                "heavy_sha256": digest(chosen),
                "shifted_rows_sha256": digest(rows),
                "cut_violation_numerators": violations,
                "maximum_cut_lower_bound": [max(violations), 1000],
            }
        )
    expected_records.sort(key=lambda r: (r["maximum_cut_lower_bound"][0], r["heavy_global_ids"]))
    for rank, row in enumerate(expected_records):
        row["rank"] = rank
    assert expected_records == proposal["candidates"]
    assert proposal["selected_first_round_ranks"] == list(range(20))
    assert proposal["proposed_budget"] == {
        "rounds_max": 3,
        "lp_evaluations_max": 60,
        "solver_seconds_max": 30,
    }
    audit = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "generator_sha256": sha(SOURCE),
        "proposal_sha256": sha(PROPOSAL),
        "bundle_sha256": sha(bundle_path),
        "complete_neighbors": len(neighbors),
        "row_sets_reconstructed": len(neighbors) + 1,
        "rows_per_set": 697,
        "ordinary_columns": 1200,
        "heavy_columns": 276,
        "per_anchor": dict(Counter(str(r["anchor"]) for r in expected_records)),
        "cut_weight_bounds": dual_weight_bounds,
        "first20_bound_numerators": [
            r["maximum_cut_lower_bound"][0] for r in expected_records[:20]
        ],
        "normalization_denominator": 1000,
        "ranking_replayed": True,
        "all_invariants_passed": True,
        "optimization_calls": 0,
        "scope": (
            "Complete two-edge switches from the fixed baseline in the declared regular family. "
            "Each cut has signed-row weights of magnitude at most1000, so its positive gap "
            "divided by1000 is a valid lower bound on the L1 elastic objective. "
            "This review does not execute or certify outcomes of the planned bounded pilot."
        ),
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit), flush=True)


if __name__ == "__main__":
    main()
