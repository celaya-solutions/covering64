# Document:    Independent Degree Nineteen Roadmap Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Recompute full link automorphisms without using supplied groups for pruning."""

import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "link-classification"
ROADMAP = HERE.parent / "degree19-roadmap"
POINTS = tuple(range(2, 17))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_blocks(path):
    blocks = [tuple(map(int, line.split()))
              for line in path.read_text().splitlines() if line.strip()]
    require(len(blocks) == 19 and len(set(blocks)) == 19, "nineteen distinct blocks required")
    require(all(len(block) == 5 and block == tuple(sorted(set(block)))
                and block[0] == 1 and all(1 <= point <= 16 for point in block)
                for block in blocks), "malformed first link")
    return {block[1:] for block in blocks}


def automorphisms(blocks):
    incidence = {size: Counter(subset for block in blocks for subset in combinations(block, size))
                 for size in range(1, 5)}
    signature = {point: (incidence[1][(point,)],
                         tuple(sorted(incidence[2][tuple(sorted((point, other)))]
                                      for other in POINTS if other != point))) for point in POINTS}
    choices = {point: [target for target in POINTS if signature[point] == signature[target]]
               for point in POINTS}
    found, nodes = [], 0

    def extend(mapping):
        nonlocal nodes
        nodes += 1
        if len(mapping) == 15:
            require({tuple(sorted(mapping[p] for p in block)) for block in blocks} == blocks,
                    "complete incidence-preserving map changed a block")
            found.append(tuple(mapping[p] for p in POINTS))
            return
        assigned = sorted(mapping)
        used = set(mapping.values())
        viable_by_point = []
        for point in POINTS:
            if point in mapping:
                continue
            viable = []
            for target in choices[point]:
                if target in used:
                    continue
                if all(incidence[size + 1][tuple(sorted((*subset, point)))] ==
                       incidence[size + 1][tuple(sorted((*(mapping[p] for p in subset), target)))]
                       for size in range(1, min(3, len(assigned)) + 1)
                       for subset in combinations(assigned, size)):
                    viable.append(target)
            if not viable:
                return
            viable_by_point.append((len(viable), point, viable))
        _, point, viable = min(viable_by_point)
        for target in viable:
            extend({**mapping, point: target})

    extend({})
    return sorted(found), nodes, incidence


def point_orbits(maps):
    # Union-find does not assume the input maps are group-closed.
    parent = {point: point for point in POINTS}

    def root(point):
        while parent[point] != point:
            point = parent[point]
        return point

    for mapping in maps:
        require(sorted(mapping) == list(POINTS), "invalid permutation")
        for point, target in zip(POINTS, mapping):
            parent[root(target)] = root(point)
    groups = {}
    for point in POINTS:
        groups.setdefault(root(point), []).append(point)
    return sorted(groups.values())


def main():
    roadmap = json.loads((ROADMAP / "orbits.json").read_text())
    supplied = json.loads((INPUT / "automorphisms.json").read_text())
    require(roadmap["automorphisms_sha256"] == sha(INPUT / "automorphisms.json"),
            "automorphism input hash changed")
    require(roadmap["source_sha256"] == sha(ROADMAP / "check.py"), "roadmap checker hash changed")
    expected_shapes = (1, 4, 44, 47)
    require(tuple(row["shape"] for row in roadmap["classes"]) == expected_shapes,
            "wrong roadmap shapes")
    require(tuple(row["shape"] for row in supplied["classes"]) == expected_shapes,
            "wrong automorphism shapes")
    reports = []
    for shape, record, saved in zip(expected_shapes, roadmap["classes"], supplied["classes"]):
        witness = INPUT / f"shape-{shape}-class-0.txt"
        require(record["witness_sha256"] == sha(witness), "witness hash changed")
        blocks = read_blocks(witness)
        maps, nodes, counts = automorphisms(blocks)
        require(counts[1][(2,)] == 6 and all(counts[1][(p,)] == 5 for p in range(3, 17)),
                "wrong link incidence degrees")
        require(all(counts[2][pair] >= 1 for pair in combinations(POINTS, 2)),
                "point link misses an outside pair")
        given = [tuple(row[str(p)] for p in POINTS) for row in saved["maps"]]
        require(len(given) == len(set(given)) and sorted(given) == maps,
                "supplied maps are not the independently enumerated full group")
        require(saved["automorphism_count"] == record["automorphism_count"] == len(maps),
                "wrong reported group order")
        orbits = point_orbits(maps)
        require(saved["point_orbits"] == record["point_orbits"] == orbits,
                "incorrect point orbits")
        high = [{"id": f"single19-shape{shape}-high21-{orbit[0]}",
                 "degree21_point": orbit[0], "orbit": orbit} for orbit in orbits]
        anchor = [{"id": f"double19-overlap5-shape{shape}-second-{orbit[0]}",
                   "second_anchor": orbit[0], "orbit": orbit} for orbit in orbits
                  if all(counts[1][(p,)] == 5 for p in orbit)]
        require(high == record["single19_cases"] and anchor == record["overlap5_cases"],
                "incorrect distinguished-point case list")
        reports.append({"shape": shape, "passed": True, "witness_sha256": sha(witness),
                        "full_automorphisms": maps, "group_order": len(maps),
                        "backtracking_nodes": nodes, "point_orbits": orbits,
                        "single19_count": len(high), "overlap5_anchor_count": len(anchor)})
    require(sum(r["single19_count"] for r in reports) == roadmap["single19_cases"] == 38,
            "wrong sole-degree19 total")
    require(sum(r["overlap5_anchor_count"] for r in reports) ==
            roadmap["overlap5_anchor_cases"] == 34, "wrong overlap-five total")
    result = {"passed": True, "classes": reports, "checker_sha256": sha(Path(__file__)),
              "roadmap_sha256": sha(ROADMAP / "orbits.json"),
              "readme_sha256": sha(ROADMAP / "README.md"),
              "scope": "Full automorphisms and point-case lists recomputed independently. "
                       "The separate four-class point-link classification is a prerequisite, "
                       "not reproved here. No cover-invariance constraint is introduced."}
    (HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": True, "single19_cases": 38, "overlap5_anchor_cases": 34,
                      "groups": [r["group_order"] for r in reports],
                      "nodes": [r["backtracking_nodes"] for r in reports]}))


if __name__ == "__main__":
    main()
