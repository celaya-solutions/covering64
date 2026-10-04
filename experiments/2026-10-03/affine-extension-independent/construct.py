# Document:    Independent Affine Norm Circle Pool Construction
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Construct the 16-point pool independently using an anisotropic GF(4) norm."""

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def mul(a, b):
    # Polynomial basis 1,w with w^2=w+1; no GF(16) arithmetic is used here.
    low = (a & 1) * (b & 1)
    middle = ((a & 1) * (b >> 1)) ^ ((a >> 1) * (b & 1))
    high = (a >> 1) * (b >> 1)
    return (low ^ high) | ((middle ^ high) << 1)


def norm(u, v):
    return mul(u, u) ^ mul(u, v) ^ mul(2, mul(v, v))


def label(u, v):
    # In the requested GF(16) polynomial labels, w=6 and theta=2.
    # z=u+v*theta. The bit shift never exceeds the degree-three basis.
    embed = [0, 1, 6, 7]
    return (embed[u] ^ (embed[v] << 1)) + 1


def construct():
    points = list(itertools.product(range(4), repeat=2))
    assert sorted(label(*point) for point in points) == list(range(1, 17))
    assert [point for point in points if norm(*point) == 0] == [(0, 0)]
    assert all(mul(a, b) == mul(b, a) for a, b in points)
    assert all(mul(a, b ^ c) == mul(a, b) ^ mul(a, c)
               for a, b, c in itertools.product(range(4), repeat=3))
    assert all(any(mul(a, b) == 1 for b in range(1, 4)) for a in range(1, 4))
    circles = {tuple(sorted(label(u, v) for u, v in points
                            if norm(u ^ center_u, v ^ center_v) == radius))
               for center_u, center_v in points for radius in range(1, 4)}
    lines = {tuple(sorted(label(u, v) for u, v in points if u == offset))
             for offset in range(4)}
    lines |= {tuple(sorted(label(u, v) for u, v in points
                           if v == mul(slope, u) ^ offset))
              for slope, offset in points}
    assert len(circles) == 48 and all(len(c) == 5 for c in circles)
    assert len(lines) == 20 and all(len(line) == 4 for line in lines)
    pair_counts = Counter(pair for line in lines for pair in itertools.combinations(line, 2))
    assert len(pair_counts) == 120 and set(pair_counts.values()) == {1}
    steiner = circles | {tuple(sorted((*line, 17))) for line in lines}
    triples17 = Counter(t for block in steiner for t in itertools.combinations(block, 3))
    assert len(steiner) == 68 and len(triples17) == 680 and set(triples17.values()) == {1}
    assert all(len(set(c) & set(line)) <= 2 for c in circles for line in lines)
    extensions = {tuple(sorted((*line, point))) for line in lines
                  for point in range(1, 17) if point not in line}
    assert len(extensions) == 240 and not (extensions & circles)
    pool = sorted(circles | extensions)
    triples16 = list(itertools.combinations(range(1, 17), 3))
    containing = [[i for i, block in enumerate(pool) if set(t) <= set(block)] for t in triples16]
    assert len(pool) == 288 and Counter(map(len, containing)) == {4: 480, 12: 80}
    collinear = {t for line in lines for t in itertools.combinations(line, 3)}
    assert len(collinear) == 80
    assert all(sum(t in collinear for t in itertools.combinations(block, 3)) == 4
               for block in extensions)
    return {"circles": sorted(circles), "lines": sorted(lines), "pool": pool,
            "steiner17": sorted(steiner), "containing": containing,
            "point_map": [[u, v, label(u, v)] for u, v in points]}


def main():
    result = construct()
    payload = json.dumps(result, separators=(",", ":")).encode()
    (HERE / "pool.json").write_bytes(payload + b"\n")
    report = {"passed": True,
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "pool_sha256": hashlib.sha256(payload + b"\n").hexdigest(),
              "construction": "GF4 anisotropic norm u^2+uv+w*v^2, affine lines and external points",
              "steiner_blocks": 68, "steiner_triples": 680, "triple_multiplicity": 1,
              "finite_circles": 48, "affine_lines": 20, "extensions": 240,
              "pool_blocks": 288, "collinear_triples": 80, "noncollinear_triples": 480,
              "scope": "Exact construction and counts only. No 64-block covering witness or "
              "completeness claim for the full 4368-block universe."}
    (HERE / "construction-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
