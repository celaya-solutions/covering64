# Document:    Derive target covers from the published C(17,6,4) witness
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      02deaf1189bf6e3419bc5204b9997fa295121f73898b6e2979858acbcd2e4146
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Reproduce the two 65-block point links; no search or novelty claim."""

import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent


def fingerprint(blocks):
    return {
        "point_degrees": sorted(Counter(p for b in blocks for p in b).values()),
        "pair_degree_histogram": dict(sorted(Counter(Counter(
            p for b in blocks for p in combinations(b, 2)).values()).items())),
        "block_intersection_histogram": dict(sorted(Counter(
            len(set(a) & set(b)) for a, b in combinations(blocks, 2)).items())),
    }


def main():
    source = HERE / "source-17-6-4-188.txt"
    blocks = [tuple(map(int, line.split())) for line in source.read_text().splitlines()
              if line.strip()]
    assert len(blocks) == len(set(blocks)) == 188
    assert all(len(b) == len(set(b)) == 6 and set(b) <= set(range(1, 18))
               for b in blocks)
    assert {t for b in blocks for t in combinations(sorted(b), 4)} == set(
        combinations(range(1, 18), 4))
    degrees = Counter(p for b in blocks for p in b)
    results = []
    for point in sorted(p for p in degrees if degrees[p] <= 65):
        remaining = [p for p in range(1, 18) if p != point]
        relabel = {p: i + 1 for i, p in enumerate(remaining)}
        link = sorted(tuple(sorted(relabel[p] for p in block if p != point))
                      for block in blocks if point in block)
        assert len(link) == len(set(link))
        assert {t for b in link for t in combinations(b, 3)} == set(
            combinations(range(1, 17), 3))
        path = HERE / f"link-at-{point}-{len(link)}.txt"
        data = "".join(" ".join(map(str, b)) + "\n" for b in link).encode()
        path.write_bytes(data)
        results.append({"source_point": point, "file": path.name,
                        "blocks": len(link), "sha256": hashlib.sha256(data).hexdigest(),
                        **fingerprint(link)})
    (HERE / "derived-links.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
