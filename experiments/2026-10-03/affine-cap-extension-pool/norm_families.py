# Document:    Six GF4 Norm Families Partitioning the Affine Five-Caps
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      5a11bb0c829a7d8ced025bd8ac817e9e03d9d256307497cf820037e7ee3a1259
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read-only exact geometry analysis; it adds no solver assumptions or constraints."""

import hashlib
import json
import subprocess
import sys
from collections import Counter
from itertools import combinations, product
from pathlib import Path

from covering64.core import canonical_text, verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mul(a, b):
    value = 0
    while b:
        if b & 1:
            value ^= a
        b >>= 1
        a <<= 1
        if a & 4:
            a ^= 7
    return value


def main():
    raw = ROOT / "experiments/scratch/affine-norm-families-20261003"
    require(not raw.exists(), "new immutable analysis directory required")
    manifest = json.loads((HERE / "manifest.json").read_text())
    pool_path = ROOT / manifest["pool"]
    require(sha(pool_path) == manifest["pool_sha256"], "frozen pool")
    pool = json.loads(pool_path.read_text())
    original = ROOT / "experiments/scratch/inversive-plane-pool-20261003/pool.json"
    require(sha(original) == manifest["source_pool_sha256"], "original circles")
    original_circles = {tuple(b) for b in json.loads(original.read_text())["retained_circles"]}
    by_block = {tuple(entry["block"]): entry for entry in pool["pool"]}
    caps = {block for block, entry in by_block.items() if entry["kind"] == "cap"}
    infinity_lines = {tuple(sorted((*line, 17))) for line in pool["affine_lines"]}
    points = list(product(range(4), repeat=2))
    embedding = [0, 1, 6, 7]
    labels = {(u, v): (embedding[u] ^ (embedding[v] << 1)) + 1 for u, v in points}
    require(set(labels.values()) == set(range(1, 17)), "point-map bijection")
    forms = [(a, c) for a, c in product(range(1, 4), repeat=2)
             if mul(a, c) ^ mul(mul(a, c), mul(a, c)) == 1]
    require(len(forms) == 6, "six normalized anisotropic forms")
    raw.mkdir(parents=True)
    (raw / "norm_families.py").write_bytes(Path(__file__).read_bytes())
    seen, reports = set(), []
    for a, c in forms:
        def q(u, v):
            return mul(a, mul(u, u)) ^ mul(u, v) ^ mul(c, mul(v, v))

        require([point for point in points if q(*point) == 0] == [(0, 0)], "anisotropy")
        family = set()
        for center in points:
            for radius in range(1, 4):
                circle = tuple(sorted(labels[(u, v)] for u, v in points
                                      if q(u ^ center[0], v ^ center[1]) == radius))
                require(len(circle) == 5, "circle size")
                family.add(circle)
        require(len(family) == 48 and family <= caps and not family & seen,
                "48 disjoint cap circles per form")
        seen |= family
        plane = family | infinity_lines
        covered = Counter(t for block in plane for t in combinations(block, 3))
        require(len(plane) == 68 and set(covered) == set(combinations(range(1, 18), 3)) and
                set(covered.values()) == {1}, "Steiner plane triple partition")
        witness = raw / f"plane-a{a}-c{c}.txt"
        witness.write_text(canonical_text(sorted(plane)))
        package = verify_cover(plane, v=17, k=5, t=3)
        checked = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check_cover.py"), str(witness),
             "--v", "17", "--k", "5", "--t", "3"],
            text=True, capture_output=True, check=False, timeout=20)
        standalone = json.loads(checked.stdout)
        require(package["valid"] and standalone["valid"] and checked.returncode == 0
                and package["blocks"] == standalone["blocks"] == 68, "plane double verification")
        for label, report in (("package", package), ("standalone", standalone)):
            (raw / f"plane-a{a}-c{c}-{label}.json").write_text(json.dumps(report, indent=2) + "\n")
        reports.append(dict(a=a, c=c, circle_count=48, steiner17_blocks=68,
                            steiner17_triples=680, triple_multiplicity=1,
                            witness_sha256=sha(witness), package_valid=True, standalone_valid=True,
                            matches_original_inversive_family=family == original_circles,
                            local_pool_ids=sorted(by_block[b]["local_id"] for b in family),
                            global_block_ids=sorted(by_block[b]["global_id"] for b in family)))
    require(seen == caps and len(caps) == 288, "complete cap partition")
    matching = [row for row in reports if row["matches_original_inversive_family"]]
    require(len(matching) == 1 and matching[0]["a"] == 1 and matching[0]["c"] == 2,
            "original norm form")
    result = dict(passed=True, source_sha256=sha(Path(__file__)), pool_sha256=sha(pool_path),
                  original_pool_sha256=sha(original), field="GF4 with omega^2=omega+1",
                  coefficient_labels={"0": "0", "1": "1", "2": "omega", "3": "omega+1"},
                  normalized_form="a*u^2+u*v+c*v^2; trace_GF4/GF2(a*c)=1",
                  point_map=[[u, v, label] for (u, v), label in labels.items()],
                  forms=reports, distinct_caps=288, pairwise_family_intersection=0,
                  common_infinity_blocks=20, solver_calls=0,
                  scope="Exact finite family decomposition only. No 64-block covering witness, "
                        "solver assumption, family-count profile or global lower bound.")
    (HERE / "norm-families.json").write_text(json.dumps(result, indent=2) + "\n")
    (raw / "norm-families.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(passed=True, forms=forms, caps=len(caps),
                         original_form=[matching[0]["a"], matching[0]["c"]])))


if __name__ == "__main__":
    main()
