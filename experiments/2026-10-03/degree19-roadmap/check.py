# Document:    Complete Degree-Nineteen Roadmap Orbit Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      c5881d4f37c7b0d9654e1acc8f99ebf8b0c39908d6688e3650f1a67ecd5e69e8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check saved full-link automorphisms and enumerate safe distinguished-point orbits."""

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder = ROOT / "experiments/2026-10-03/link-classification"
    auto_path = folder / "automorphisms.json"
    supplied = json.loads(auto_path.read_text())
    result = {"source_sha256": digest(Path(__file__)), "automorphisms_sha256": digest(auto_path),
              "scope": "Valid full-link automorphism orbits preserve existence; four-class "
                       "completeness comes from the separately replayed degree19 classification.",
              "classes": []}
    for record in supplied["classes"]:
        shape = record["shape"]
        witness_path = folder / f"shape-{shape}-class-0.txt"
        blocks = {tuple(map(int, line.split())) for line in witness_path.read_text().splitlines()
                  if line.strip()}
        assert len(blocks) == 19 and all(block[0] == 1 and len(block) == 5 for block in blocks)
        degrees = Counter(point for block in blocks for point in block if point != 1)
        assert degrees[2] == 6 and all(degrees[point] == 5 for point in range(3, 17))
        maps = {tuple(int(mapping[str(point)]) for point in range(2, 17))
                for mapping in record["maps"]}
        assert len(maps) == record["automorphism_count"]
        assert tuple(range(2, 17)) in maps
        for mapping in maps:
            assert sorted(mapping) == list(range(2, 17))
            assert {tuple(sorted((1, *(mapping[point - 2] for point in block[1:]))))
                    for block in blocks} == blocks
            for other in maps:
                assert tuple(mapping[point - 2] for point in other) in maps
        pending = set(range(2, 17))
        orbits = []
        while pending:
            first = min(pending)
            orbit = sorted({mapping[first - 2] for mapping in maps})
            assert set(orbit) <= pending
            pending -= set(orbit)
            orbits.append(orbit)
        assert orbits == record["point_orbits"]
        result["classes"].append({
            "shape": shape, "witness_sha256": digest(witness_path),
            "automorphism_count": len(maps), "point_orbits": orbits,
            "single19_cases": [{"id": f"single19-shape{shape}-high21-{orbit[0]}",
                                "degree21_point": orbit[0], "orbit": orbit} for orbit in orbits],
            "overlap5_cases": [{"id": f"double19-overlap5-shape{shape}-second-{orbit[0]}",
                                 "second_anchor": orbit[0], "orbit": orbit}
                                for orbit in orbits if 2 not in orbit],
        })
    result["single19_cases"] = sum(len(row["single19_cases"]) for row in result["classes"])
    result["overlap5_anchor_cases"] = sum(len(row["overlap5_cases"]) for row in result["classes"])
    assert result["single19_cases"] == 38 and result["overlap5_anchor_cases"] == 34
    Path(__file__).with_name("orbits.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"single19_cases": result["single19_cases"],
                      "overlap5_anchor_cases": result["overlap5_anchor_cases"]}))


if __name__ == "__main__":
    main()
