# Document:    Equivalence of the Six Affine Norm Circle Families
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      4caf31875d67fc0996ee1a0c589a165568b5aa3f118a61e92a258cb9ce232135
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Save direct point maps from every circle family to the original family."""

import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def validate(source, target, lines, permutation):
    assert sorted(permutation) == list(range(1, 17))
    assert len(source) == len(target) == 48 and len(lines) == 20
    assert {tuple(sorted(permutation[x - 1] for x in line)) for line in lines} == set(lines)
    mapped = [tuple(sorted(permutation[x - 1] for x in circle)) for circle in source]
    assert set(mapped) == set(target)
    lookup = {circle: i for i, circle in enumerate(target)}
    return [lookup[circle] for circle in mapped]


def main():
    spec = importlib.util.spec_from_file_location("independent_geometry", HERE / "check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    lines, families = module.construct()
    target = families[(1, 2)]
    coordinates = {module.label(u, v): (u, v) for u, v in itertools.product(range(4), repeat=2)}
    all_maps = []
    for a, b, c, d in itertools.product(range(4), repeat=4):
        if module.mul(a, d) ^ module.mul(b, c) == 0:
            continue
        permutation = []
        for point in range(1, 17):
            u, v = coordinates[point]
            permutation.append(
                module.label(
                    module.mul(a, u) ^ module.mul(b, v), module.mul(c, u) ^ module.mul(d, v)
                )
            )
        assert sorted(permutation) == list(range(1, 17))
        assert {tuple(sorted(permutation[x - 1] for x in line)) for line in lines} == set(lines)
        all_maps.append(([a, b, c, d], permutation))
    assert len(all_maps) == 180
    witnesses = []
    for form, circles in families.items():
        good = []
        for matrix, permutation in all_maps:
            mapped = {tuple(sorted(permutation[x - 1] for x in circle)) for circle in circles}
            if mapped == set(target):
                good.append((matrix, permutation))
        assert len(good) == 30
        matrix, permutation = good[0]
        block_map = validate(circles, target, lines, permutation)
        witnesses.append(
            {
                "source_form": list(form),
                "target_form": [1, 2],
                "valid_linear_maps": len(good),
                "matrix_row_major": matrix,
                "point_images_one_based": permutation,
                "circle_images_zero_based": block_map,
            }
        )
    damaged = [
        ([1] * 16, families[(1, 2)]),
        ([0] + list(range(2, 17)), families[(1, 2)]),
        (list(range(1, 16)), families[(1, 2)]),
        (list(range(1, 17)), families[(1, 3)]),
    ]
    for permutation, source in damaged:
        try:
            validate(source, target, lines, permutation)
        except AssertionError:
            continue
        raise AssertionError("damaged map accepted")
    report = {
        "passed": True,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "geometry_source_sha256": hashlib.sha256((HERE / "check.py").read_bytes()).hexdigest(),
        "invertible_linear_maps": len(all_maps),
        "witnesses": witnesses,
        "damaged_maps_rejected": len(damaged),
        "solver_calls": 0,
        "scope": "Each individual circle-family pool is isomorphic to the original; "
        "does not identify the union of six families with an individual family.",
    }
    (HERE / "family-equivalence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "witnesses"}))


if __name__ == "__main__":
    main()
