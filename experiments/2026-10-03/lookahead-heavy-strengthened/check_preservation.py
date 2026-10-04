# Document:    Independent Pair and Triple Preservation Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      7b1d37decb95748b3b82ddaf94a44fca9f5942d1296c2cf36514188c199032af
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import itertools as it
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    base = HERE.parent / "lookahead-heavy-completion/manifest.json"
    data = json.loads(base.read_text())
    heavy = list(map(tuple, data["heavy_blocks"]))
    ordinary = list(map(tuple, data["ordinary_blocks"]))
    anchors = [set(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
    hubs = (4, 8, 12, 16)
    hpairs = list(it.combinations(hubs, 2))
    pair_count = Counter(p for b in heavy for p in it.combinations(b, 2))
    triple_count = Counter(t for b in heavy for t in it.combinations(b, 3))
    limits = {}
    for group in anchors:
        hub = max(group) + 1
        for a in group:
            for b in range(1, 17):
                if b == a:
                    continue
                pair = tuple(sorted((a, b)))
                lower = 7 if b in group else 6 if b == hub else 5
                assert pair not in limits or limits[pair] == lower
                limits[pair] = lower
            # The seven own heavy blocks force two peer-pair counts at least seven.
            assert all(pair_count[tuple(sorted((a, b)))] == 7 for b in group - {a})
            # Two distinct repeated triples force the own-hub pair count at least six.
            assert all(triple_count[tuple(sorted((a, b, hub)))] == 2 for b in group - {a})
            assert 7 + 7 + 6 + 12 * 5 == 4 * 20
            assert sum(v for p, v in limits.items() if a in p) == 80
    assert len(limits) == 114
    # Every hub has anchor incidence 3*6 + 9*5 = 63, leaving hub-pair sum 17.
    assert all(sum(v for p, v in limits.items() if h in p) == 63 for h in hubs)
    assert 4 * 20 - 63 - 3 * 5 == 2
    graphs = []
    for values in it.product(range(3), repeat=6):
        if all(sum(v for p, v in zip(hpairs, values, strict=True) if h in p) == 2 for h in hubs):
            graphs.append(values)
    assert len(graphs) == 6
    assert Counter(tuple(sorted(v for v in values if v)) for values in graphs) == {
        (1, 1, 1, 1): 3,
        (2, 2): 3,
    }
    nonheavy = [t for t in it.combinations(range(1, 17), 3) if set(t) not in anchors]
    assert len(nonheavy) == 556
    fixed = 0
    for triple in nonheavy:
        support = [b for b in ordinary if set(triple) <= set(b)]
        if not support:
            assert triple_count[triple] in (1, 2)
            fixed += 1
            continue
        for graph in graphs:
            full = {**limits, **{p: 5 + v for p, v in zip(hpairs, graph, strict=True)}}
            assert any(full[p] == 5 for p in it.combinations(triple, 2))
    receipt = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "base_manifest_sha256": sha(base),
        "anchor_pair_equalities": 114,
        "hub_residual_graphs": [list(v) for v in graphs],
        "hub_pair_order": hpairs,
        "four_cycles": 3,
        "doubled_matchings": 3,
        "nonheavy_triples": 556,
        "already_fixed_triples": fixed,
        "remaining_triples_checked_against_every_hub_graph": 556 - fixed,
        "scope": "Necessary consequences of coverage, degree20 and the fixed regular "
        "four-sevenfold heavy templates. Not an unrestricted reduction.",
    }
    (HERE / "preservation-audit.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
