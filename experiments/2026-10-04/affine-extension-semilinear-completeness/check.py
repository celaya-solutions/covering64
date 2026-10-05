# Document:    Four-Class Affine Extension Recipe Completeness Certificate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      71e029bfcdf8ea3a2d87789ca6eab58114ca1f22af7896ae7724c481497ddb51
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Finite group/function verification; no optimizer and no covering search."""

import gzip
import json
import platform
import subprocess
import time
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import combinations, permutations, product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
CLASSES = BASE / "clebsch-point-link-construction/classes.json"
AUTOMORPHISMS = BASE / "circulant-chosen-link-catalog/canonical-images.json"
REPRESENTATIVES = BASE / "affine-extension-point-variants/representatives.json"
FIBERS = BASE / "circulant-chosen-link-catalog/link-fibers.json"
OLD_SUMMARY = BASE / "circulant-chosen-link-catalog/summary.json"
SCRATCH = ROOT / "experiments/scratch/affine-extension-semilinear-completeness-v1.0.0"
EXPECTED = {
    CLASSES: "6916b285c1c53693b4f2f53bd0194afd6f2c936e1a10da3a236c5311ab86a2cc",
    AUTOMORPHISMS: "18a7eff11931df2dc25c17e2beb3ccb588c6fe29aaf753ece024c20e59607f8b",
    REPRESENTATIVES: "2db5cd79692f83847e2951fb13b08acb72d4e7b9e7f3fdba1557f931a69b9a7d",
}
QUADS = tuple(combinations(range(1, 16), 4))
QUAD_RANK = {quad: index for index, quad in enumerate(QUADS)}
PERMS = tuple(permutations(range(5)))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(value):
    return sha256(canonical(value)).hexdigest()


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def mul(a, b):
    """Polynomial multiplication modulo x^2+x+1; integers encode coefficients."""
    result = 0
    while b:
        if b & 1:
            result ^= a
        a <<= 1
        if a & 4:
            a ^= 7
        b >>= 1
    return result


def semilinear_geometry(classes):
    points = tuple(p for p in product(range(4), repeat=2) if p != (0, 0))
    labels = {p: index + 1 for index, p in enumerate(points)}
    directions = ((1, 0), (1, 1), (1, 2), (1, 3), (0, 1))
    rays = tuple(
        tuple(sorted(labels[mul(t, x), mul(t, y)] for t in (1, 2, 3))) for x, y in directions
    )
    lines = set()
    for x, y in directions:
        for a, b in product(range(4), repeat=2):
            line = {(a ^ mul(t, x), b ^ mul(t, y)) for t in range(4)}
            if (0, 0) not in line:
                lines.add(tuple(sorted(labels[p] for p in line)))
    require(len(lines) == 15, "fifteen off-origin affine lines")
    for model in classes.values():
        require(tuple(map(tuple, model["ag_points_by_label"])) == points, "point labels")
        require(tuple(map(tuple, model["rays_by_zero_based_index"])) == rays, "ray labels")
        require(set(map(tuple, model["retained_ag_blocks"])) == lines, "retained lines")
    ray_ids = {ray: index for index, ray in enumerate(rays)}
    rows = []
    for a, b, c, d in product(range(4), repeat=4):
        determinant = mul(a, d) ^ mul(b, c)
        if determinant == 0:
            continue
        for epsilon in (0, 1):
            transformed = []
            for x, y in points:
                if epsilon:
                    x, y = mul(x, x), mul(y, y)
                transformed.append(labels[mul(a, x) ^ mul(b, y), mul(c, x) ^ mul(d, y)])
            require(sorted(transformed) == list(range(1, 16)), "point bijection")
            ray_permutation = [
                ray_ids[tuple(sorted(transformed[v - 1] for v in ray))] for ray in rays
            ]
            require(
                {tuple(sorted(transformed[v - 1] for v in line)) for line in lines} == lines,
                "all retained affine lines preserved",
            )
            rows.append(
                {
                    "matrix_row_major": [a, b, c, d],
                    "frobenius_exponent": epsilon,
                    "determinant": determinant,
                    "point_permutation_one_based": transformed,
                    "ray_permutation_zero_based": ray_permutation,
                }
            )
    ray_counts = Counter(tuple(row["ray_permutation_zero_based"]) for row in rows)
    require(len(rows) == 360, "360 invertible semilinear maps")
    require(len({tuple(r["point_permutation_one_based"]) for r in rows}) == 360, "distinct maps")
    require(set(ray_counts) == set(PERMS), "full S5 induced on the five rays")
    require(set(ray_counts.values()) == {3}, "three scalar lifts of each ray permutation")
    return rows


def conjugate(function, permutation):
    transformed = [None] * 5
    for i in range(5):
        transformed[permutation[i]] = permutation[function[i]]
    return tuple(transformed)


def classify_functions(classes, maps):
    representatives = {
        name: tuple(data["function_images_zero_based"]) for name, data in classes.items()
    }
    representatives["triangle-coincident-leaves-outside-scope"] = (1, 2, 0, 0, 0)
    for name, model in classes.items():
        core_edges = {
            tuple(v - 1 for v in edge) for edge in model["canonical_excess_edges"] if max(edge) <= 5
        }
        function_edges = {tuple(sorted((i, j))) for i, j in enumerate(representatives[name])}
        require(
            any(
                {tuple(sorted(p[v] for v in edge)) for edge in function_edges} == core_edges
                for p in PERMS
            ),
            "fixed function has the stated undirected core class",
        )
    ray_lifts = {}
    for index, row in enumerate(maps):
        ray_lifts.setdefault(tuple(row["ray_permutation_zero_based"]), index)
    classification = {}
    for name, representative in representatives.items():
        for permutation in PERMS:
            source = conjugate(representative, permutation)
            inverse = tuple(permutation.index(i) for i in range(5))
            require(conjugate(source, inverse) == representative, "conjugacy direction")
            require(source not in classification or classification[source][0] == name, "disjoint")
            classification.setdefault(source, (name, inverse, ray_lifts[inverse]))
    rows = []
    excluded = Counter()
    for function in product(range(5), repeat=5):
        if any(function[i] == i for i in range(5)):
            excluded["loop"] += 1
            continue
        if any(function[function[i]] == i for i in range(5)):
            excluded["directed_two_cycle"] += 1
            continue
        require(function in classification, "complete function classification")
        name, permutation, map_index = classification[function]
        rows.append(
            {
                "function_zero_based": function,
                "class": name,
                "in_four_class_scope": name in classes,
                "to_representative_ray_permutation_zero_based": permutation,
                "semilinear_map_index": map_index,
                "representative_function_zero_based": representatives[name],
            }
        )
    require(len(rows) == len(classification) == 444, "all 444 admissible functions")
    require(sum(r["in_four_class_scope"] for r in rows) == 384, "384 four-class functions")
    return rows, dict(excluded)


def complete_automorphisms(model, supplied):
    edges = {tuple(edge) for edge in model["canonical_excess_edges"]}
    degrees = Counter(v for edge in edges for v in edge)
    core = tuple(v for v in range(1, 16) if degrees[v] == 4)
    require(core == tuple(range(1, 6)), "canonical center set")
    require(all(degrees[v] == 1 for v in range(6, 16)), "ten degree-one leaves")
    core_edges = {edge for edge in edges if set(edge) <= set(core)}
    leaves = {v: tuple(w for w in range(6, 16) if tuple(sorted((v, w))) in edges) for v in core}
    complete = set()
    for target_core in permutations(core):
        mapping = dict(zip(core, target_core))
        if {tuple(sorted(mapping[v] for v in edge)) for edge in core_edges} != core_edges:
            continue
        for choices in product(*(permutations(leaves[mapping[v]]) for v in core)):
            full = dict(mapping)
            for v, target_leaves in zip(core, choices):
                full.update(zip(leaves[v], target_leaves))
            permutation = tuple(full[v] for v in range(1, 16))
            require(
                {tuple(sorted(full[v] for v in edge)) for edge in edges} == edges,
                "constructed complete E automorphism",
            )
            complete.add(permutation)
    saved = [tuple(row["canonical_permutation"]) for row in supplied]
    require(len(set(saved)) == len(saved) and set(saved) == complete, "complete saved E group")
    return sorted(complete)


def image_unions(classes, supplied, representatives):
    receipts, unions = {}, {}
    for name, model in classes.items():
        automorphisms = complete_automorphisms(model, supplied[name])
        quad_actions = [
            tuple(QUAD_RANK[tuple(sorted(p[v - 1] for v in quad))] for quad in QUADS)
            for p in automorphisms
        ]
        union = set()
        receipts[name] = []
        for index, representative in enumerate(representatives[name]):
            ids = tuple(representative["quad_ids"])
            require(
                tuple(map(tuple, representative["blocks"])) == tuple(QUADS[i] for i in ids),
                "saved representative uses lexicographic quad IDs",
            )
            images = {tuple(sorted(action[i] for i in ids)) for action in quad_actions}
            stabilizers = [
                p
                for p, action in zip(automorphisms, quad_actions)
                if tuple(sorted(action[i] for i in ids)) == ids
            ]
            require(len(images) * len(stabilizers) == len(automorphisms), "orbit stabilizer")
            require(not union.intersection(images), "disjoint representative orbits")
            union.update(images)
            receipts[name].append(
                {
                    "representative_index": index,
                    "representative_quad_ids": ids,
                    "image_count": len(images),
                    "stabilizer_count": len(stabilizers),
                    "stabilizers_one_based": stabilizers,
                    "sorted_image_union_sha256": digest(sorted(images)),
                    "old_witness_orbit": representative["old_witness_orbit"],
                }
            )
        require(len(union) == 5184, "5184 distinct canonical-E families per class")
        old_images = {
            tuple(sorted(QUAD_RANK[tuple(block)] for block in row["canonical_blocks"]))
            for row in supplied[name]
        }
        require(old_images <= union, "expanded union contains every original chosen witness image")
        require(
            sum(row["old_witness_orbit"] for row in receipts[name]) == 1,
            "exactly one original witness orbit per class",
        )
        unions[name] = sorted(union)
    return receipts, unions


def workload(fibers, unions, old_summary, classes, supplied):
    memberships = [p for fiber in fibers for p in fiber["profile_ids"]]
    require(sorted(memberships) == list(range(1300)), "fibers partition the 1300 profiles")
    require(len(fibers) == 38, "38 actual E fibers")
    keys = [tuple(map(tuple, fiber["actual_excess_edges"])) for fiber in fibers]
    require(len(set(keys)) == 38, "distinct actual excess graphs prevent cross-fiber duplicates")
    counts = defaultdict(lambda: {"fibers": 0, "profiles": 0, "links": 0, "profile_link_pairs": 0})
    rows = []
    for fiber in fibers:
        name = fiber["class"]
        mapping = fiber["canonical_to_actual"]
        require(sorted(mapping) == list(range(2, 17)), "fiber map is a point bijection")
        require(
            {
                tuple(sorted(mapping[v - 1] for v in edge))
                for edge in classes[name]["canonical_excess_edges"]
            }
            == set(map(tuple, fiber["actual_excess_edges"])),
            "fiber E transport",
        )
        nlinks, nprofiles = len(unions[name]), len(fiber["profile_ids"])
        counts[name]["fibers"] += 1
        counts[name]["profiles"] += nprofiles
        counts[name]["links"] += nlinks
        counts[name]["profile_link_pairs"] += nlinks * nprofiles
        rows.append(
            {
                "excess_link_id": fiber["excess_link_id"],
                "class": name,
                "profiles": nprofiles,
                "links": nlinks,
                "profile_link_pairs": nlinks * nprofiles,
            }
        )
    links = sum(row["links"] for row in counts.values())
    pairs = sum(row["profile_link_pairs"] for row in counts.values())
    require(links == 196992 and pairs == 6739200, "expanded point-one workload")
    require(
        sum(len(supplied[f["class"]]) for f in fibers)
        == old_summary["distinct_chosen_link_images"],
        "old catalog link baseline",
    )
    require(
        sum(len(supplied[f["class"]]) * len(f["profile_ids"]) for f in fibers)
        == old_summary["profile_link_pairs"],
        "old catalog pair baseline",
    )
    return {
        "by_class": dict(counts),
        "by_fiber": rows,
        "distinct_point_one_link_families": links,
        "compatible_profile_link_pairs": pairs,
        "additional_link_families": links - old_summary["distinct_chosen_link_images"],
        "additional_profile_link_pairs": pairs - old_summary["profile_link_pairs"],
        "one_pass_support_row_popcount_upper_bound": pairs * 455,
        "one_pass_zero_row_union_upper_bound": pairs * 80,
        "expanded_actual_catalog_materialized": False,
    }


def main():
    started = time.monotonic()
    require(not (HERE / "summary.json").exists(), "existing evidence remains frozen")
    for path, expected in EXPECTED.items():
        require(sha256(path.read_bytes()).hexdigest() == expected, f"frozen input {path.name}")
    classes, supplied, representatives, fibers, old_summary = (
        json.loads(path.read_text())
        for path in (CLASSES, AUTOMORPHISMS, REPRESENTATIVES, FIBERS, OLD_SUMMARY)
    )
    maps = semilinear_geometry(classes)
    functions, excluded = classify_functions(classes, maps)
    receipts, unions = image_unions(classes, supplied, representatives)
    counts = workload(fibers, unions, old_summary, classes, supplied)
    for name, value in (
        ("semilinear-maps.json", maps),
        ("function-conjugacies.json", functions),
        ("orbit-certificates.json", receipts),
        ("workload.json", counts),
    ):
        dump(name, value)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    raw_path = SCRATCH / "canonical-image-unions.json.gz"
    require(not raw_path.exists(), "existing raw union remains frozen")
    raw_path.write_bytes(gzip.compress(canonical(unions), mtime=0))
    summary = {
        "scope": "AG(2,4) origin-deletion recipe with distinct centers and four saved core types",
        "recipe_completeness_proved": True,
        "all_affine_constructions_claimed": False,
        "all_local_decompositions_claimed": False,
        "extension_settings_audit_delegated_separately": True,
        "invertible_GF4_matrices": 180,
        "semilinear_maps": len(maps),
        "ray_permutations": 120,
        "scalar_lifts_per_ray_permutation": 3,
        "function_domain_size": 3125,
        "excluded_functions": excluded,
        "admissible_function_counts": dict(Counter(r["class"] for r in functions)),
        "four_class_admissible_functions": 384,
        "canonical_image_counts": {name: len(rows) for name, rows in unions.items()},
        "orbit_size_histograms": {
            name: dict(Counter(row["image_count"] for row in rows))
            for name, rows in receipts.items()
        },
        "point_one_link_families": counts["distinct_point_one_link_families"],
        "profile_link_pairs": counts["compatible_profile_link_pairs"],
        "optimizer_calls": 0,
        "cover_search_calls": 0,
        "cover_found": False,
        "elapsed_seconds": time.monotonic() - started,
        "python_version": platform.python_version(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_hashes": {
            str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
            for path in (CLASSES, AUTOMORPHISMS, REPRESENTATIVES, FIBERS, OLD_SUMMARY)
        },
        "output_hashes": {
            name: sha256((HERE / name).read_bytes()).hexdigest()
            for name in (
                "semilinear-maps.json",
                "function-conjugacies.json",
                "orbit-certificates.json",
                "workload.json",
            )
        },
        "raw_union": str(raw_path.relative_to(ROOT)),
        "raw_union_sha256": sha256(raw_path.read_bytes()).hexdigest(),
        "raw_union_uncompressed_canonical_sha256": digest(unions),
    }
    dump("summary.json", summary)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
