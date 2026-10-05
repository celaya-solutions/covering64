# Document:    Affine Recipe Certificate Replay and Damage Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      259020b932165784d2b900017a14af2355c9fe2bff61d299aa658d01e9d6a4c8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay saved certificates using a fixed field table, without importing check.py."""

import copy
import gzip
import json
import time
from collections import Counter
from hashlib import sha256
from itertools import combinations, product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
TABLE = ((0, 0, 0, 0), (0, 1, 2, 3), (0, 2, 3, 1), (0, 3, 1, 2))
POINTS = tuple(p for p in product(range(4), repeat=2) if p != (0, 0))
LABELS = {p: i + 1 for i, p in enumerate(POINTS)}
QUADS = tuple(combinations(range(1, 16), 4))
RANK = {quad: i for i, quad in enumerate(QUADS)}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text())


def check_maps(rows, classes):
    expected = {
        (a, b, c, d, epsilon)
        for a, b, c, d in product(range(4), repeat=4)
        if TABLE[a][d] ^ TABLE[b][c]
        for epsilon in (0, 1)
    }
    actual = [(*row["matrix_row_major"], row["frobenius_exponent"]) for row in rows]
    require(len(actual) == len(set(actual)) and set(actual) == expected, "complete map parameters")
    rays = classes["C5"]["rays_by_zero_based_index"]
    lines = {tuple(line) for line in classes["C5"]["retained_ag_blocks"]}
    for row in rows:
        a, b, c, d = row["matrix_row_major"]
        require(row["determinant"] == TABLE[a][d] ^ TABLE[b][c], "determinant")
        expected_points = []
        for x, y in POINTS:
            if row["frobenius_exponent"]:
                x, y = TABLE[x][x], TABLE[y][y]
            expected_points.append(LABELS[TABLE[a][x] ^ TABLE[b][y], TABLE[c][x] ^ TABLE[d][y]])
        require(row["point_permutation_one_based"] == expected_points, "field-map evaluation")
        permutation = row["ray_permutation_zero_based"]
        for i, ray in enumerate(rays):
            require(sorted(expected_points[v - 1] for v in ray) == rays[permutation[i]], "ray map")
        require(
            {tuple(sorted(expected_points[v - 1] for v in line)) for line in lines} == lines,
            "retained affine lines",
        )
    counts = Counter(tuple(row["ray_permutation_zero_based"]) for row in rows)
    require(len(counts) == 120 and set(counts.values()) == {3}, "all ray permutations")


def check_functions(rows, maps, classes):
    expected = {
        f for f in product(range(5), repeat=5) if all(f[i] != i and f[f[i]] != i for i in range(5))
    }
    actual = [tuple(row["function_zero_based"]) for row in rows]
    require(len(actual) == len(set(actual)) and set(actual) == expected, "complete function domain")
    for row in rows:
        function = row["function_zero_based"]
        permutation = row["to_representative_ray_permutation_zero_based"]
        require(
            permutation == maps[row["semilinear_map_index"]]["ray_permutation_zero_based"],
            "explicit semilinear lift",
        )
        name = row["class"]
        representative = (
            classes[name]["function_images_zero_based"] if name in classes else [1, 2, 0, 0, 0]
        )
        require(row["representative_function_zero_based"] == representative, "fixed function")
        require(row["in_four_class_scope"] == (name in classes), "function scope")
        for i in range(5):
            require(representative[permutation[i]] == permutation[function[i]], "conjugacy")
    require(
        Counter(row["class"] for row in rows)
        == {
            "C5": 24,
            "C4-leaf": 120,
            "triangle-path2": 120,
            "triangle-two-leaves": 120,
            "triangle-coincident-leaves-outside-scope": 60,
        },
        "five function classes",
    )


def check_orbits(receipts, unions, automorphisms):
    for name, rows in receipts.items():
        actions = [row["canonical_permutation"] for row in automorphisms[name]]
        seen = set()
        for index, row in enumerate(rows):
            require(row["representative_index"] == index, "orbit index")
            ids = tuple(row["representative_quad_ids"])
            images = []
            for permutation in actions:
                images.append(
                    tuple(
                        sorted(
                            RANK[tuple(sorted(permutation[v - 1] for v in QUADS[i]))] for i in ids
                        )
                    )
                )
            unique = set(images)
            stabilizers = {tuple(p) for p, image in zip(actions, images) if image == ids}
            require(len(unique) == row["image_count"], "orbit size")
            require(len(stabilizers) == row["stabilizer_count"], "stabilizer size")
            require(stabilizers == set(map(tuple, row["stabilizers_one_based"])), "stabilizers")
            require(digest(sorted(unique)) == row["sorted_image_union_sha256"], "orbit digest")
            require(not seen.intersection(unique), "orbit disjointness")
            seen.update(unique)
        saved = list(map(tuple, unions[name]))
        require(len(saved) == len(set(saved)) == 5184 and seen == set(saved), "full image union")


def main():
    started = time.monotonic()
    require(not (HERE / "replay.json").exists(), "existing replay remains frozen")
    summary = load(HERE / "summary.json")
    for relative, expected in summary["input_hashes"].items():
        require(sha256((ROOT / relative).read_bytes()).hexdigest() == expected, "frozen input")
    for relative, expected in summary["output_hashes"].items():
        require(sha256((HERE / relative).read_bytes()).hexdigest() == expected, "frozen output")
    raw = (ROOT / summary["raw_union"]).read_bytes()
    require(sha256(raw).hexdigest() == summary["raw_union_sha256"], "frozen raw union")
    unions = json.loads(gzip.decompress(raw))
    require(digest(unions) == summary["raw_union_uncompressed_canonical_sha256"], "union digest")
    maps = load(HERE / "semilinear-maps.json")
    functions = load(HERE / "function-conjugacies.json")
    receipts = load(HERE / "orbit-certificates.json")
    classes = load(BASE / "clebsch-point-link-construction/classes.json")
    automorphisms = load(BASE / "circulant-chosen-link-catalog/canonical-images.json")
    check_maps(maps, classes)
    check_functions(functions, maps, classes)
    check_orbits(receipts, unions, automorphisms)
    controls = []

    def rejects(name, action):
        try:
            action()
        except (ValueError, KeyError, IndexError) as error:
            controls.append({"control": name, "rejected": True, "reason": str(error)})
        else:
            raise ValueError(f"damage control accepted: {name}")

    damaged_maps = copy.deepcopy(maps)
    damaged_maps[0]["point_permutation_one_based"][0] = 0
    rejects("damaged point permutation", lambda: check_maps(damaged_maps, classes))
    rejects("missing semilinear map", lambda: check_maps(maps[1:], classes))
    damaged_functions = copy.deepcopy(functions)
    damaged_functions[0]["semilinear_map_index"] = (
        damaged_functions[0]["semilinear_map_index"] + 2
    ) % len(maps)
    rejects("wrong semilinear lift", lambda: check_functions(damaged_functions, maps, classes))
    rejects("missing function", lambda: check_functions(functions[1:], maps, classes))
    damaged_receipts = copy.deepcopy(receipts)
    damaged_receipts["C4-leaf"][0]["image_count"] += 1
    rejects("false orbit size", lambda: check_orbits(damaged_receipts, unions, automorphisms))
    damaged_unions = copy.deepcopy(unions)
    damaged_unions["C4-leaf"].pop()
    rejects("missing union image", lambda: check_orbits(receipts, damaged_unions, automorphisms))
    result = {
        "complete_replay": True,
        "semilinear_maps": len(maps),
        "functions": len(functions),
        "representative_orbits": sum(map(len, receipts.values())),
        "canonical_families": sum(map(len, unions.values())),
        "damage_controls": controls,
        "elapsed_seconds": time.monotonic() - started,
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "summary_sha256": sha256((HERE / "summary.json").read_bytes()).hexdigest(),
        "optimizer_calls": 0,
        "cover_search_calls": 0,
    }
    (HERE / "replay.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
