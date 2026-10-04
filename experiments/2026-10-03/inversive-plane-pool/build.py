# Document:    GF16 Inversive Plane and Affine Extension Pool
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      f76dba0da2f77edd2d4bf42d54006d6a723068783bdcc0ad86ecc1405e3e6cce
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Construct and verify a restricted pool; export an exact64 CP model without solving."""

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from itertools import combinations, product
from pathlib import Path

from ortools import __version__ as ortools_version
from ortools.sat.python import cp_model

from covering64.core import canonical_text, verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/inversive-plane-pool-20261003"


def require(value, message):
    if not value:
        raise ValueError(message)


def mul(a, b):
    value = 0
    while b:
        if b & 1:
            value ^= a
        b >>= 1
        a <<= 1
        if a & 16:
            a ^= 0x13
    return value


def power(a, n):
    value = 1
    for _ in range(n):
        value = mul(value, a)
    return value


def image(matrix, point):
    a, b, c, d = matrix
    if point == 17:
        numerator, denominator = a, c
    else:
        z = point - 1
        numerator, denominator = mul(a, z) ^ b, mul(c, z) ^ d
    return 17 if denominator == 0 else 1 + mul(numerator, power(denominator, 14))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def double_check(blocks, name, v):
    path = RAW / f"{name}.txt"
    path.write_text(canonical_text(blocks))
    package = verify_cover(blocks, v=v, k=5, t=3)
    independent_run = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_cover.py"), str(path),
         "--v", str(v), "--k", "5", "--t", "3"],
        cwd=ROOT, text=True, capture_output=True, check=False, timeout=20)
    independent = json.loads(independent_run.stdout)
    require(package["valid"] and independent["valid"] and independent_run.returncode == 0
            and package["blocks"] == independent["blocks"] == len(blocks), "positive control")
    save(RAW / f"{name}-package.json", package)
    save(RAW / f"{name}-standalone.json", independent)
    return dict(blocks=len(blocks), sha256=sha(path), package_valid=True, standalone_valid=True)


def main():
    require(not RAW.exists(), "new immutable raw directory required")
    require(all(mul(a, power(a, 14)) == 1 for a in range(1, 16)), "field inverses")
    require(all(mul(a, b) == mul(b, a) for a, b in product(range(16), repeat=2)),
            "commutativity")
    require(all(mul(a, b ^ c) == mul(a, b) ^ mul(a, c)
                for a, b, c in product(range(16), repeat=3)), "distributivity")
    subfield = [a for a in range(16) if power(a, 4) == a]
    require(subfield == [0, 1, 6, 7], "GF4 subfield")
    subline = [17, *[a + 1 for a in subfield]]
    multiplicities = Counter()
    matrices = []
    for matrix in product(range(16), repeat=4):
        if next((value for value in matrix if value), 0) != 1:
            continue
        a, b, c, d = matrix
        if mul(a, d) ^ mul(b, c) == 0:
            continue
        images = [image(matrix, point) for point in range(1, 18)]
        require(sorted(images) == list(range(1, 18)), "projective map not a permutation")
        block = tuple(sorted(image(matrix, point) for point in subline))
        multiplicities[block] += 1
        matrices.append(matrix)
    plane = sorted(multiplicities)
    require(len(matrices) == 4080 and len(plane) == 68 and
            set(multiplicities.values()) == {60}, "PGL orbit counts")
    all_triples = set(combinations(range(1, 18), 3))
    covered = Counter(t for block in plane for t in combinations(block, 3))
    require(set(covered) == all_triples and set(covered.values()) == {1},
            "Steiner triple partition")
    lines = sorted(tuple(p for p in b if p != 17) for b in plane if 17 in b)
    circles = sorted(b for b in plane if 17 not in b)
    require(len(lines) == 20 and len(circles) == 48, "affine decomposition")
    pairs = Counter(pair for line in lines for pair in combinations(line, 2))
    require(set(pairs) == set(combinations(range(1, 17), 2)) and
            set(pairs.values()) == {1}, "affine pair partition")
    require(max(len(set(line) & set(circle)) for line in lines for circle in circles) == 2,
            "line-circle intersection")
    extensions = {tuple(sorted((*line, point))): index
                  for index, line in enumerate(lines)
                  for point in range(1, 17) if point not in line}
    require(len(extensions) == 240 and not set(extensions) & set(circles), "extension distinctness")
    pool = sorted([*circles, *extensions])
    global_ids = {b: i for i, b in enumerate(combinations(range(1, 17), 5))}
    triples = list(combinations(range(1, 17), 3))
    supports = [[i for i, b in enumerate(pool) if set(t) <= set(b)] for t in triples]
    collinear = {t for line in lines for t in combinations(line, 3)}
    require(len(collinear) == 80 and len(pool) == 288, "pool dimensions")
    require(all(len(support) == (12 if triple in collinear else 4)
                for triple, support in zip(triples, supports, strict=True)), "triple support sizes")
    model = cp_model.CpModel()
    variables = [model.new_bool_var(f"block_{global_ids[block]}") for block in pool]
    model.add(sum(variables) == 64)
    for support in supports:
        model.add(sum(variables[i] for i in support) >= 1)
    require(not model.validate(), "CP validation")
    RAW.mkdir(parents=True)
    (RAW / "build.py").write_bytes(Path(__file__).read_bytes())
    model_path = RAW / "exact64.pbtxt"
    require(model.export_to_file(str(model_path)), "CP export")
    data = dict(field=dict(modulus="x^4+x+1", modulus_bits=19, finite_label="z+1",
                           infinity=17, subfield=subfield, theta=2,
                           multiplication=[[mul(a, b) for b in range(16)] for a in range(16)]),
                subline=subline, normalized_matrix_count=len(matrices),
                plane_blocks=plane, plane_orbit_multiplicity=60,
                affine_lines=lines, retained_circles=circles,
                pool=[dict(local_id=i, global_id=global_ids[b], block=b,
                           kind="line_extension" if b in extensions else "circle",
                           line_id=extensions.get(b)) for i, b in enumerate(pool)],
                triples=triples, supports=supports,
                collinear_triples=sorted(collinear))
    save(RAW / "pool.json", data)
    positive = sorted([*circles, *[tuple(sorted((*line, min(set(range(1, 17)) - set(line)))))
                                  for line in lines]])
    require(len(set(positive)) == len(positive) == 68 and set(positive) <= set(pool),
            "68-block control pool membership")
    checks = dict(plane17=double_check(plane, "plane17-68", 17),
                  pool68=double_check(positive, "pool16-68", 16))
    manifest = dict(version="v1.0.0", created_utc=datetime.now(UTC).isoformat(),
                    source_revision=subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                            cwd=ROOT, text=True).strip(),
                    builder_sha256=sha(Path(__file__)), ortools_version=ortools_version,
                    pool=str((RAW / "pool.json").relative_to(ROOT)),
                    pool_sha256=sha(RAW / "pool.json"),
                    model=str(model_path.relative_to(ROOT)), model_sha256=sha(model_path),
                    variables=288, rows=561, target_blocks=64, circles=48, extensions=240,
                    affine_lines=20, collinear_triples=80, noncollinear_triples=480,
                    triple_support_distribution=dict(Counter(map(len, supports))),
                    global_variable_order="Increasing global lexicographic five-block IDs",
                    positive_controls=checks, solver_calls=0,
                    scope="Only the 288-block algebraic pool. No symmetry, incidence profile, "
                          "circle-count or extension-count restriction; "
                          "no global completeness claim.")
    save(HERE / "manifest.json", manifest)
    save(RAW / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
