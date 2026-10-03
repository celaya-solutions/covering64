# Document:    Standalone core automorphism and removal-orbit verification
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Verify a subgroup of the fixed core and enumerate its removal-case orbits."""

import argparse
import json
from collections import Counter, deque
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent


def compute():
    certificate = json.loads((HERE / "fixed-core-certificate.json").read_text())
    core = sorted(tuple(b) for b in certificate["core_blocks"])
    assert len(core) == len(set(core)) == 60
    data = json.loads((HERE / "core-automorphisms.json").read_text())
    assert certificate["core_sha256"] == data["core_sha256"]
    generators = [tuple(g) for g in data["generators_images_of_1_to_16"]]
    identity = tuple(range(1, 17))
    assert all(sorted(g) == list(identity) for g in generators)
    seen, queue = {identity}, deque([identity])
    while queue:
        current = queue.popleft()
        for generator in generators:
            composed = tuple(generator[v - 1] for v in current)
            if composed not in seen:
                seen.add(composed)
                queue.append(composed)
        assert len(seen) <= 60, "Unexpectedly large subgroup"
    assert len(seen) == 60
    block_index = {block: i + 1 for i, block in enumerate(core)}
    actions = []
    for values in sorted(seen):
        images = [tuple(sorted(values[p - 1] for p in b)) for b in core]
        assert set(images) == set(core)
        action = [block_index[b] for b in images]
        assert sorted(action) == list(range(1, 61))
        actions.append({"point_images_1_based": values, "block_images_1_based": action})
    removal_results = {}
    for size in (1, 2, 3):
        unseen = set(combinations(range(1, 61), size))
        original_count = len(unseen)
        orbits = []
        while unseen:
            representative = min(unseen)
            orbit = {tuple(sorted(a["block_images_1_based"][i - 1] for i in representative))
                     for a in actions}
            assert orbit <= unseen
            unseen -= orbit
            orbits.append({"representative_block_indices_1_based": representative,
                           "orbit_size": len(orbit)})
        assert sum(o["orbit_size"] for o in orbits) == original_count
        removal_results[str(size)] = {
            "total_removal_sets": original_count, "orbit_count": len(orbits),
            "orbit_size_histogram": dict(sorted(Counter(o["orbit_size"] for o in orbits).items())),
            "orbits": orbits,
        }
    return {
        "scope": "Subgroup of automorphisms of the exact fixed core; no unrestricted claim",
        "core_sha256": certificate["core_sha256"],
        "core_block_order": "Lexicographically sorted core_blocks; block indices are 1-based",
        "core_blocks": core, "subgroup_order_independently_enumerated": len(seen),
        "group_actions": actions, "removal_orbits": removal_results,
    }


def main():
    if not __debug__:
        raise SystemExit("Run without Python -O; assertions must be enabled")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--certificate", type=Path, default=HERE / "core-removal-orbits.json")
    args = parser.parse_args()
    expected = json.loads(json.dumps(compute()))
    if args.write:
        args.certificate.write_text(json.dumps(expected, indent=2) + "\n")
    assert json.loads(args.certificate.read_text()) == expected, "Damaged orbit certificate"
    print(json.dumps({"verified": True, "subgroup_order": 60,
                      "removal_orbit_counts": {k: v["orbit_count"]
                                               for k, v in expected["removal_orbits"].items()}}))


if __name__ == "__main__":
    main()
