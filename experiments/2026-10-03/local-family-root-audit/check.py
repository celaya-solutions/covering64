# Document:    Independent Local Family Isomorphism Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      b1ae82f5937dd5634fd1060ea1566f43be6a51e147d1f8ec13a44912d14cf87f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check all independently enumerated families and explicit class bijections."""

import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

import networkx as nx

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "local-family-classification"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inspect(blocks):
    require(len(blocks) == 13, "wrong cardinality")
    require(
        all(
            len(b) == 4 and len(set(b)) == 4 and all(type(p) is int and 1 <= p <= 13 for p in b)
            for b in blocks
        ),
        "malformed block",
    )
    canonical = sorted(tuple(sorted(b)) for b in blocks)
    require(len(set(canonical)) == 13, "duplicate block")
    degree = Counter(p for b in canonical for p in b)
    require(degree == Counter({p: 4 for p in range(1, 14)}), "wrong degree")
    pairs = Counter(t for b in canonical for t in combinations(b, 2))
    holes = [t for t in combinations(range(1, 14), 2) if pairs[t] == 0]
    require(
        all(n <= 1 for n in Counter(p for t in holes for p in t).values()),
        "holes are not a matching",
    )
    return canonical, holes


def graph(blocks):
    blocks, holes = inspect(blocks)
    graph = nx.Graph()
    damaged_points = {p for pair in holes for p in pair}
    for p in range(1, 14):
        graph.add_node((0, p), kind=0, defect=int(p in damaged_points))
    for i, block in enumerate(blocks):
        graph.add_node((1, i), kind=1, defect=-1)
        graph.add_edges_from(((0, p), (1, i)) for p in block)
    return graph


def verify_map(blocks, target, mapping):
    require(
        set(mapping) == set(range(1, 14)) and set(mapping.values()) == set(range(1, 14)),
        "point map is not a bijection",
    )
    mapped = {tuple(sorted(mapping[p] for p in b)) for b in blocks}
    require(mapped == set(target), "point map does not carry every block")


def main():
    replay_file = HERE / "replay.json"
    replay = json.loads(replay_file.read_text())
    require(replay["complete"] is True and len(replay["patterns"]) == 26, "replay is incomplete")
    representatives = {}
    for i in range(3):
        raw = (SOURCE / f"enumeration-family-{i:03}.txt").read_text()
        blocks, holes = inspect([list(map(int, line.split())) for line in raw.splitlines()])
        representatives[len(holes)] = blocks
    require(set(representatives) == {0, 4, 6}, "unexpected representatives")
    targets = {r: graph(b) for r, b in representatives.items()}
    maps, histogram = [], Counter()
    for pattern in replay["patterns"]:
        require(pattern["complete"] is True, "unfinished pattern")
        for solution in pattern["families"]:
            blocks, holes = inspect(solution)
            r = len(holes)
            require(r in targets, "new class needs review")
            matcher = nx.algorithms.isomorphism.GraphMatcher(
                graph(blocks),
                targets[r],
                node_match=lambda a, b: (a["kind"], a["defect"]) == (b["kind"], b["defect"]),
            )
            require(matcher.is_isomorphic(), "family not isomorphic to proposed representative")
            mapping = {p: matcher.mapping[(0, p)][1] for p in range(1, 14)}
            verify_map(blocks, representatives[r], mapping)
            histogram[r] += 1
            maps.append(
                {"pattern": pattern["pattern"], "holes": r, "blocks": blocks, "point_map": mapping}
            )
    require(histogram == Counter({0: 72, 4: 8, 6: 8}), "family count mismatch")
    controls = []
    original = representatives[4]
    damaged = [list(b) for b in original]
    damaged[1] = damaged[0]
    try:
        inspect(damaged)
    except ValueError:
        controls.append("duplicate_block")
    damaged = [list(b) for b in original]
    damaged[0][0] = 14
    try:
        inspect(damaged)
    except ValueError:
        controls.append("out_of_range_point")
    mapping = {p: p for p in range(1, 14)}
    mapping[1] = 2
    try:
        verify_map(original, original, mapping)
    except ValueError:
        controls.append("nonbijective_map")
    require(len(controls) == 3, "damage control accepted")
    result = {
        "status": "PASS",
        "library": f"networkx {nx.__version__}",
        "replay_sha256": hashlib.sha256(replay_file.read_bytes()).hexdigest(),
        "enumerator_sha256": hashlib.sha256((SOURCE / "replay.cpp").read_bytes()).hexdigest(),
        "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "patterns": 26,
        "labelled_families": 88,
        "unmarked_classes": 3,
        "family_hole_counts": dict(histogram),
        "damage_controls_rejected": controls,
        "scope": "13 quadruples on13 points, all degrees4, matching holes; not a64-cover",
        "explicit_maps": maps,
    }
    (HERE / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "explicit_maps"}))


if __name__ == "__main__":
    main()
