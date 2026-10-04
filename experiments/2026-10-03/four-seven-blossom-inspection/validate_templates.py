"""Document:    Exhaustive Integer Heavy-Link Blossom Template Validation
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      b36bf028a7e5cefde3d561ffa9aba412b266d7722753d0ab5e9398ff48556044
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
"""

import hashlib
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import four_seven_blossom_cuts as cuts  # noqa: E402


def pairings(vertices, forbidden):
    if not vertices:
        yield ()
        return
    first = min(vertices)
    rest = vertices - {first}
    for second in sorted(rest):
        if (first, second) not in forbidden:
            for tail in pairings(rest - {second}, forbidden):
                yield ((first, second),) + tail


def main():
    outside = tuple(range(4, 17))
    edges = tuple(itertools.combinations(outside, 2))
    edge_ids = {edge: index for index, edge in enumerate(edges)}
    forbidden = {edge for group in (range(5, 8), range(9, 12), range(13, 16))
                 for edge in itertools.combinations(group, 2)}
    subsets = list(cuts.templates(0))
    matrix = np.asarray([[int(a in subset and b in subset) for a, b in edges]
                         for subset, _ in subsets], dtype=np.int16).T
    bounds = np.asarray([upper for _, upper in subsets], dtype=np.int16)
    seen = set()
    max_excess = -100
    tight_template_counts = np.zeros(len(subsets), dtype=np.int32)
    for leaves in itertools.combinations(range(5, 17), 2):
        for tail in pairings(set(range(5, 17)) - set(leaves), forbidden):
            graph = tuple(sorted(((4, leaves[0]), (4, leaves[1]), *tail)))
            assert graph not in seen
            seen.add(graph)
            degree = Counter(point for edge in graph for point in edge)
            assert degree == Counter({point: 2 if point == 4 else 1 for point in outside})
            assert not (set(graph) & forbidden)
            totals = matrix[[edge_ids[edge] for edge in graph]].sum(axis=0)
            excess = totals - bounds
            assert max(excess) <= 0
            max_excess = max(max_excess, int(max(excess)))
            tight_template_counts += (excess == 0)
    assert len(seen) == 29970
    transports = []
    for group in range(4):
        points = [((point - 1 + 4 * group) % 16) + 1 for point in range(1, 17)]
        inverse = [points.index(point) + 1 for point in range(1, 17)]
        target = dict(cuts.templates(group))
        for subset, upper in subsets:
            mapped = tuple(sorted(points[point - 1] for point in subset))
            assert target[mapped] == upper
            original_edges = set(itertools.combinations(subset, 2))
            mapped_edges = {tuple(sorted(points[point - 1] for point in edge))
                            for edge in original_edges}
            assert mapped_edges == set(itertools.combinations(mapped, 2))
        transports.append({"target_group": group, "point_permutation": points,
                           "inverse": inverse, "template_bijection": True})
    summary = {
        "scope": "Exhaustive check of valid labeled heavy-link templates and exact transports; "
                 "odd-set validity itself follows from the elementary degree parity proof.",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "helper_sha256": hashlib.sha256(Path(cuts.__file__).read_bytes()).hexdigest(),
        "labeled_links": len(seen), "templates_per_group": len(subsets),
        "direct_integer_inequality_checks": len(seen) * len(subsets),
        "checks_validated_through_four_exact_transports": len(seen) * len(subsets) * 4,
        "maximum_integer_excess": max_excess,
        "templates_attaining_equality": int(np.count_nonzero(tight_template_counts)),
        "transports": transports,
        "transport_scope": "Generic degree/odd-set templates; these maps need not preserve "
                           "every hub-pair case because each target link is proved directly.",
    }
    Path(__file__).with_name("template-validation.json").write_text(
        json.dumps(summary, indent=2) + "\n")
    print(json.dumps({key: value for key, value in summary.items() if key != "transports"},
                     indent=2))


if __name__ == "__main__":
    main()
