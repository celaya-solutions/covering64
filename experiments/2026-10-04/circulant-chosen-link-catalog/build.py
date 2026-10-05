# Document:    Circulant Catalog of Images of Four Chosen Point Links
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      23af0b7730047e092af212e524f95289164fa92ba312e6d9eb3d898dc64d570e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Finite catalog only: all excess-graph isomorphism images of four witnesses."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import combinations, permutations, product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PROFILE_DIR = HERE.parent / "circulant-all-excess-profiles"
CONSTRUCTION = HERE.parent / "clebsch-point-link-construction"
BLOCKS = tuple(combinations(range(1, 17), 5))
RANK = {block: index for index, block in enumerate(BLOCKS)}
TRIPLES = tuple(combinations(range(1, 17), 3))
CLASS_KEYS = {
    ((2, 2, 2, 2, 2), 0): "C5",
    ((1, 2, 2, 2, 3), 0): "C4-leaf",
    ((1, 2, 2, 2, 3), 1): "triangle-path2",
    ((1, 1, 2, 3, 3), 1): "triangle-two-leaves",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def canonical_bytes(rows):
    return "".join(" ".join(map(str, row)) + "\n" for row in sorted(rows)).encode("ascii")


def dump(name, data, compact=False):
    (HERE / name).write_text(
        json.dumps(
            data,
            indent=None if compact else 2,
            separators=(",", ":") if compact else None,
            sort_keys=True,
        )
        + "\n"
    )


def classify(edges):
    edges = set(edges)
    degrees = Counter(point for edge in edges for point in edge)
    require(sorted(degrees.values()) == [1] * 10 + [4] * 5, "heavy and leaf degrees")
    heavy = {point for point, degree in degrees.items() if degree == 4}
    core = {edge for edge in edges if set(edge) <= heavy}
    require(len(core) == 5, "five core edges")
    sequence = tuple(sorted(sum(point in edge for edge in core) for point in heavy))
    triangles = sum(
        all(pair in core for pair in combinations(triple, 2))
        for triple in combinations(sorted(heavy), 3)
    )
    require((sequence, triangles) in CLASS_KEYS, "one of four chosen classes")
    return CLASS_KEYS[(sequence, triangles)]


def canonicalize(edges):
    edges = set(edges)
    degrees = Counter(point for edge in edges for point in edge)
    heavy = sorted(point for point, degree in degrees.items() if degree == 4)
    core = [edge for edge in edges if set(edge) <= set(heavy)]
    choices = []
    for order in permutations(heavy):
        mapping = {point: index + 1 for index, point in enumerate(order)}
        transformed = tuple(sorted(tuple(sorted(mapping[x] for x in edge)) for edge in core))
        choices.append((transformed, order))
    _, order = min(choices)
    mapping = {point: index + 1 for index, point in enumerate(order)}
    for point in order:
        leaves = sorted(
            other
            for other, degree in degrees.items()
            if degree == 1 and tuple(sorted((point, other))) in edges
        )
        for leaf in leaves:
            mapping[leaf] = len(mapping) + 1
    require(
        set(mapping) == set(range(2, 17)) and set(mapping.values()) == set(range(1, 16)),
        "complete point-one map",
    )
    transformed = tuple(sorted(tuple(sorted(mapping[x] for x in edge)) for edge in edges))
    return transformed, mapping


def automorphisms(data):
    edges = {tuple(edge) for edge in data["canonical_excess_edges"]}
    core = {edge for edge in edges if max(edge) <= 5}
    leaves = {h: sorted(v for v in range(6, 16) if (h, v) in edges) for h in range(1, 6)}
    images = {}
    count = 0
    for order in permutations(range(1, 6)):
        if {tuple(sorted(order[x - 1] for x in edge)) for edge in core} != core:
            continue
        if any(len(leaves[h]) != len(leaves[order[h - 1]]) for h in leaves):
            continue
        for groups in product(*(permutations(leaves[order[h - 1]]) for h in range(1, 6))):
            mapping = {h: order[h - 1] for h in range(1, 6)}
            for h, group in zip(range(1, 6), groups):
                mapping.update(zip(leaves[h], group))
            require(set(mapping.values()) == set(range(1, 16)), "automorphism bijection")
            require(
                {tuple(sorted(mapping[x] for x in edge)) for edge in edges} == edges,
                "automorphism preserves excess",
            )
            blocks = tuple(
                sorted(
                    tuple(sorted(mapping[x] for x in block)) for block in data["canonical_blocks"]
                )
            )
            image = {
                "canonical_permutation": [mapping[x] for x in range(1, 16)],
                "canonical_blocks": blocks,
                "canonical_sha256": sha256(canonical_bytes(blocks)).hexdigest(),
            }
            if blocks in images:
                require(
                    images[blocks]["canonical_permutation"] == image["canonical_permutation"],
                    "chosen witness has trivial stabilizer",
                )
            images[blocks] = image
            count += 1
    require(count == len(images), "all automorphism images are distinct")
    return [images[blocks] for blocks in sorted(images)]


def main():
    geometry = json.loads((PROFILE_DIR / "geometry.json").read_text())
    masks = json.loads((PROFILE_DIR / "profiles.json").read_text())["choice_masks"]
    require(
        len(masks) == len(set(masks)) == 1300 and masks == sorted(masks),
        "1300 distinct supplied profiles",
    )
    graph = {tuple(edge) for edge in geometry["edges"]}
    require(len(graph) == 40, "forty graph edges")
    classes = json.loads((CONSTRUCTION / "classes.json").read_text())
    images = {name: automorphisms(data) for name, data in classes.items()}
    require(
        {name: len(rows) for name, rows in images.items()}
        == {"C5": 320, "C4-leaf": 96, "triangle-path2": 96, "triangle-two-leaves": 144},
        "chosen witness image counts",
    )
    dump("canonical-images.json", images, compact=True)
    by_link = defaultdict(list)
    profile_rows = []
    point_census = Counter()
    for profile_id, mask in enumerate(masks):
        profile = {tuple(sorted((a, b, choices[0]))) for a, b, choices in geometry["forced"]} | {
            tuple(sorted((a, b, choices[(mask >> index) & 1])))
            for index, (a, b, choices) in enumerate(geometry["choices"])
        }
        require(len(profile) == 80, "eighty excess triples")
        pair_counts = Counter(pair for triple in profile for pair in combinations(triple, 2))
        require(
            all(
                pair_counts[pair] == (4 if pair in graph else 1)
                for pair in combinations(range(1, 17), 2)
            ),
            "every profile pair row",
        )
        for point in range(1, 17):
            link = tuple(
                sorted(
                    tuple(x for x in triple if x != point) for triple in profile if point in triple
                )
            )
            point_census[classify(link)] += 1
            if point == 1:
                by_link[link].append(profile_id)
        profile_rows.append(
            {
                "profile_id": profile_id,
                "choice_mask": mask,
                "canonical_sha256": sha256(canonical_bytes(profile)).hexdigest(),
                "excess_triples": sorted(profile),
            }
        )
    dump("profiles.json", profile_rows, compact=True)
    fibers = []
    catalog = []
    profile_link_pairs = 0
    for link_id, (edges, profile_ids) in enumerate(sorted(by_link.items())):
        name = classify(edges)
        canonical_edges, mapping = canonicalize(edges)
        require(
            canonical_edges
            == tuple(tuple(edge) for edge in classes[name]["canonical_excess_edges"]),
            "canonical class excess graph",
        )
        inverse = {value: key for key, value in mapping.items()}
        start = len(catalog)
        distinct = set()
        for image_id, image in enumerate(images[name]):
            local = sorted(
                tuple(sorted(inverse[x] for x in block)) for block in image["canonical_blocks"]
            )
            pairs = Counter(pair for block in local for pair in combinations(block, 2))
            require(
                all(pairs[pair] == 1 + (pair in edges) for pair in combinations(range(2, 17), 2)),
                "all exact mapped pair rows",
            )
            outside = Counter(triple for block in local for triple in combinations(block, 3))
            require(
                len(outside) == 80 and set(outside.values()) == {1},
                "eighty distinct outside triples",
            )
            partial = sorted((1, *block) for block in local)
            ids = tuple(RANK[block] for block in partial)
            require(
                len(ids) == len(set(ids)) == 20 and ids not in distinct,
                "twenty distinct partial blocks and unique image",
            )
            distinct.add(ids)
            catalog.append(
                {
                    "partial_id": len(catalog),
                    "excess_link_id": link_id,
                    "canonical_image_id": image_id,
                    "global_block_ids": ids,
                    "partial_canonical_sha256": sha256(canonical_bytes(partial)).hexdigest(),
                }
            )
        fibers.append(
            {
                "excess_link_id": link_id,
                "class": name,
                "actual_excess_edges": edges,
                "actual_to_canonical": [[x, mapping[x]] for x in range(2, 17)],
                "canonical_to_actual": [inverse[x] for x in range(1, 16)],
                "profile_ids": profile_ids,
                "partial_id_range_half_open": [start, len(catalog)],
            }
        )
        profile_link_pairs += len(profile_ids) * len(distinct)
    require(
        len(fibers) == 38 and len(catalog) == 5536 and profile_link_pairs == 195296,
        "full finite workload census",
    )
    require(
        len({tuple(row["global_block_ids"]) for row in catalog}) == len(catalog),
        "global partial deduplication",
    )
    dump("link-fibers.json", fibers)
    dump("partial-catalog.json", catalog, compact=True)
    summary = {
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": sha(__file__),
        "python_version": sys.version,
        "inputs": {
            str(path.relative_to(ROOT)): sha(path)
            for path in [
                PROFILE_DIR / "geometry.json",
                PROFILE_DIR / "profiles.json",
                CONSTRUCTION / "classes.json",
            ]
        },
        "point_one": 1,
        "supplied_profiles": len(masks),
        "full_point_link_census": dict(point_census),
        "point_one_excess_graphs": len(fibers),
        "point_one_excess_graph_classes": dict(Counter(fiber["class"] for fiber in fibers)),
        "profile_fiber_sizes": dict(
            sorted(Counter(len(fiber["profile_ids"]) for fiber in fibers).items())
        ),
        "chosen_witness_automorphism_image_counts": {
            name: len(rows) for name, rows in images.items()
        },
        "distinct_chosen_link_images": len(catalog),
        "profile_link_pairs": profile_link_pairs,
        "one_pass_support_row_popcount_upper_bound": profile_link_pairs * 455,
        "one_pass_zero_row_union_upper_bound": profile_link_pairs * 80,
        "remaining_block_domain_per_pair": 3003,
        "residual_rows_per_pair": 455,
        "screening_launched": False,
        "optimizer_calls": 0,
        "search_calls": 0,
        "completeness": (
            "All excess-graph isomorphism images of the FOUR specific saved canonical twenty-K4 "
            "witnesses, for the 38 point-one excess graphs in the supplied 1300 profiles. "
            "This is not a catalog of all affine constructions or all local decompositions."
        ),
        "constructive_next_step": (
            "One finite support pass across the195296 exact(profile,partial) pairs, "
            "with an explicit "
            "wall budget and saved cursor. Keep every surviving choice; do not pin an arbitrary "
            "single map before testing profile compatibility."
        ),
    }
    dump("summary.json", summary)
    print(
        json.dumps(
            {
                key: summary[key]
                for key in (
                    "point_one_excess_graphs",
                    "distinct_chosen_link_images",
                    "profile_link_pairs",
                    "one_pass_support_row_popcount_upper_bound",
                    "screening_launched",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
