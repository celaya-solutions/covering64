# Document:    Constructive Clebsch Point Link Certificates
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      7c3d272a1bc0d6cccb4aee14bd8c81c89ee781e5ab9a578878c983a7a5f70b23
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Save exact affine-plane witnesses and all recipe-to-witness bijections.

No optimization or search solver is imported or launched. Canonicalization
enumerates only the 120 permutations of the five heavy vertices.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from collections import Counter
from hashlib import sha256
from itertools import combinations, permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PROFILE = ROOT / (
    "experiments/2026-10-03/independent-geometry/independent-audit-seed-profiles.json"
)
SEEDS = [0, 1, 9, 40, 19, 8, 4, 18, 16, 12, 3, 10, 11, 26, 60, 25]
FUNCTIONS = {
    "C5": [1, 2, 3, 4, 0],
    "C4-leaf": [1, 2, 3, 0, 0],
    "triangle-path2": [1, 2, 0, 0, 3],
    "triangle-two-leaves": [1, 2, 0, 0, 1],
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def canonical_bytes(rows):
    return "".join(" ".join(map(str, row)) + "\n" for row in sorted(rows)).encode("ascii")


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonicalize(edges, vertices):
    edges = {tuple(sorted(edge)) for edge in edges}
    degrees = Counter(point for edge in edges for point in edge)
    require(sorted(degrees.values()) == [1] * 10 + [4] * 5, "excess degree pattern")
    heavy = sorted(point for point in vertices if degrees[point] == 4)
    core = [edge for edge in edges if set(edge) <= set(heavy)]
    require(len(core) == 5, "five core edges")
    choices = []
    for order in permutations(heavy):
        mapping = {point: index + 1 for index, point in enumerate(order)}
        mapped_core = tuple(sorted(tuple(sorted(mapping[x] for x in edge)) for edge in core))
        choices.append((mapped_core, order))
    _, order = min(choices)
    mapping = {point: index + 1 for index, point in enumerate(order)}
    for point in order:
        leaves = sorted(
            other
            for other in vertices
            if degrees[other] == 1 and tuple(sorted((point, other))) in edges
        )
        for leaf in leaves:
            mapping[leaf] = len(mapping) + 1
    require(set(mapping) == set(vertices), "bijection domain")
    require(set(mapping.values()) == set(range(1, 16)), "bijection range")
    mapped = tuple(sorted(tuple(sorted(mapping[x] for x in edge)) for edge in edges))
    return mapped, mapping


def mul(a, b):
    result = 0
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & 4:
            a ^= 7
    return result


def construct(function):
    points = [(x, y) for x in range(4) for y in range(4) if (x, y) != (0, 0)]
    labels = {point: index + 1 for index, point in enumerate(points)}
    lines = [
        {(x, mul(slope, x) ^ offset) for x in range(4)} for slope in range(4) for offset in range(4)
    ]
    lines += [{(offset, y) for y in range(4)} for offset in range(4)]
    rays = [sorted(labels[p] for p in line if p != (0, 0)) for line in lines if (0, 0) in line]
    retained = [tuple(sorted(labels[p] for p in line)) for line in lines if (0, 0) not in line]
    require(len(retained) == 15 and len(rays) == 5, "affine line partition")
    centers = []
    for index, image in enumerate(function):
        require(image != index and function[image] != index, "no short function cycles")
        centers.append(min(set(rays[image]) - set(centers)))
    extended = [tuple(sorted((*ray, center))) for ray, center in zip(rays, centers)]
    blocks = sorted(retained + extended)
    counts = Counter(pair for block in blocks for pair in combinations(block, 2))
    require(len(blocks) == len(set(blocks)) == 20, "twenty distinct K4 blocks")
    require(len(counts) == 105 and set(counts.values()) == {1, 2}, "all exact pair rows")
    excess = {pair for pair, count in counts.items() if count == 2}
    require(len(excess) == 15, "fifteen excess edges")
    canonical_excess, mapping = canonicalize(excess, range(1, 16))
    canonical_blocks = sorted(tuple(sorted(mapping[x] for x in block)) for block in blocks)
    triangles = [
        triple
        for triple in combinations(range(1, 16), 3)
        if all(pair in canonical_excess for pair in combinations(triple, 2))
    ]
    triangle_counts = [sum(set(t) <= set(block) for block in canonical_blocks) for t in triangles]
    require(all(count <= 1 for count in triangle_counts), "triangle caps")
    ids = {block: index for index, block in enumerate(combinations(range(1, 16), 4))}
    return {
        "function_images_zero_based": function,
        "ag_points_by_label": points,
        "rays_by_zero_based_index": rays,
        "centers_by_zero_based_ray": centers,
        "retained_ag_blocks": retained,
        "extended_ag_blocks": extended,
        "ag_to_canonical": [[x, mapping[x]] for x in range(1, 16)],
        "canonical_blocks": canonical_blocks,
        "canonical_block_variable_ids_zero_based_lex": [ids[b] for b in canonical_blocks],
        "canonical_excess_edges": canonical_excess,
        "canonical_triangle_caps": triangles,
        "triangle_block_counts": triangle_counts,
        "canonical_block_sha256": sha256(canonical_bytes(canonical_blocks)).hexdigest(),
    }


def main():
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    independent = load_module(ROOT / "scripts/check_cover.py", "independent_cover_check")
    profiles = json.loads(PROFILE.read_text())
    require(set(profiles) == set(map(str, SEEDS)), "all sixteen profile seeds")
    classes = {name: construct(function) for name, function in FUNCTIONS.items()}
    by_excess = {tuple(data["canonical_excess_edges"]): name for name, data in classes.items()}
    require(len(by_excess) == 4, "four distinct core classes")
    save("classes.json", classes)
    for name, data in classes.items():
        (OUT / f"{name}-canonical-k4.txt").write_bytes(canonical_bytes(data["canonical_blocks"]))
    vertices = tuple(range(1, 17))
    bits = [value for value in range(32) if value.bit_count() % 2 == 0]
    links = []
    representatives = {}
    class_counts = Counter()
    profile_class_counts = {}
    for seed in SEEDS:
        excess_global = {tuple(row) for row in profiles[str(seed)]}
        require(len(excess_global) == 80, "profile size")
        source_profile_hash = sha256(canonical_bytes(excess_global)).hexdigest()
        per_profile = Counter()
        for point in vertices:
            others = tuple(x for x in vertices if x != point)
            excess = {
                tuple(x for x in triple if x != point)
                for triple in excess_global
                if point in triple
            }
            canonical_excess, actual_to_canonical = canonicalize(excess, others)
            name = by_excess[canonical_excess]
            class_counts[name] += 1
            per_profile[name] += 1
            canonical_to_actual = {value: key for key, value in actual_to_canonical.items()}
            local = [
                tuple(sorted(canonical_to_actual[x] for x in block))
                for block in classes[name]["canonical_blocks"]
            ]
            pair_counts = Counter(pair for block in local for pair in combinations(block, 2))
            require(
                all(pair_counts[pair] == 1 + (pair in excess) for pair in combinations(others, 2)),
                "mapped exact pair rows",
            )
            heavy = {x for x in others if sum(x in e for e in excess) == 4}
            neighbors = {x for x in others if (bits[x - 1] ^ bits[point - 1]).bit_count() == 4}
            require(heavy == neighbors, "heavy vertices are Clebsch neighbors")
            caps = [
                tuple(sorted(canonical_to_actual[x] for x in triple))
                for triple in classes[name]["canonical_triangle_caps"]
            ]
            require(
                all(t not in excess_global for t in caps), "triangle caps have global demand one"
            )
            outside_counts = Counter(t for block in local for t in combinations(block, 3))
            residual = {
                t: 1 + (t in excess_global) - outside_counts[t] for t in combinations(others, 3)
            }
            require(
                min(residual.values()) >= 0 and sum(residual.values()) == 440,
                "nonnegative residual demands",
            )
            require(
                len(outside_counts) == 80 and max(outside_counts.values()) == 1,
                "eighty distinct outside triples",
            )
            partial = sorted(tuple(sorted((point, *block))) for block in local)
            partial_hash = sha256(canonical_bytes(partial)).hexdigest()
            link = {
                "profile_seed": seed,
                "point": point,
                "class": name,
                "source_profile_canonical_sha256": source_profile_hash,
                "actual_to_canonical": [[x, actual_to_canonical[x]] for x in others],
                "canonical_to_actual": [canonical_to_actual[x] for x in range(1, 16)],
                "actual_triangle_caps": caps,
                "residual_histogram": dict(sorted(Counter(residual.values()).items())),
                "remaining_block_count": 44,
                "partial_canonical_sha256": partial_hash,
            }
            links.append(link)
            if name not in representatives:
                package = verify_cover(partial)
                standalone = independent.verify_cover(partial, expected_blocks=20)
                require(
                    package["blocks"] == standalone["blocks"] == 20, "representative cardinality"
                )
                require(
                    package["covered"] == standalone["covered_subsets"] == 185,
                    "representative coverage",
                )
                require(
                    len(package["uncovered"]) == standalone["uncovered_count"] == 375,
                    "representative holes",
                )
                require(
                    package["canonical_sha256"] == standalone["canonical_sha256"] == partial_hash,
                    "verifier hash agreement",
                )
                require(not package["valid"] and not standalone["valid"], "partial is not a cover")
                (OUT / f"{name}-actual-partial.txt").write_bytes(canonical_bytes(partial))
                save(f"{name}-package-verifier.json", package)
                save(f"{name}-standalone-verifier.json", standalone)
                representatives[name] = {
                    "profile_seed": seed,
                    "point": point,
                    "sha256": partial_hash,
                }
        profile_class_counts[str(seed)] = dict(sorted(per_profile.items()))
    save("recipe-point-maps.json", links)
    require(
        dict(class_counts)
        == {"C5": 16, "C4-leaf": 80, "triangle-path2": 80, "triangle-two-leaves": 80},
        "class census",
    )
    summary = {
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "python_version": sys.version,
        "input_file": str(PROFILE.relative_to(ROOT)),
        "input_sha256": digest(PROFILE),
        "producer_sha256": digest(Path(__file__)),
        "package_verifier_sha256": digest(ROOT / "src/covering64/core.py"),
        "standalone_verifier_sha256": digest(ROOT / "scripts/check_cover.py"),
        "class_counts": dict(class_counts),
        "profile_class_counts": profile_class_counts,
        "representatives": representatives,
        "verified_recipe_point_maps": len(links),
        "exact_pair_rows_per_map": 105,
        "outside_residual_rows_per_map": 455,
        "local_variables_zero_based_lex": 1365,
        "all_pair_rows_and_triangle_caps_passed": True,
        "all_outside_residuals_nonnegative": True,
        "solver_calls": 0,
        "solver_seconds": 0,
        "planned_local_cp_calls_canceled": True,
        "global_existence_conclusion": (
            "None: local feasibility does not imply compatible global links."
        ),
        "scope": (
            "Four local isomorphism classes and all 256 links "
            "of the sixteen audited recipe profiles."
        ),
    }
    save("summary.json", summary)
    print(
        json.dumps(
            {
                key: summary[key]
                for key in ("class_counts", "verified_recipe_point_maps", "solver_calls")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
