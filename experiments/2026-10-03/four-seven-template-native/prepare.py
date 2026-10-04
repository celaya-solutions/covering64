# Document:    Complete Template Native Catalog and Seed Preparation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      b27492c5b42ba6df3a72a7f8cf16646bbac88b59bedbc02849b33c5002d568ee
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Export frozen108 catalogs and construct degree-correct ordinary orbit seeds."""

import gzip
import hashlib
import itertools as it
import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/four-seven-template-native-v1.0.0"
CATALOGS = ROOT / "experiments/scratch/four-seven-template-hull-refresh-108-20261003"
ANCHORS = [set(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
TRIPLES = list(it.combinations(range(1, 17), 3))
TRANK = {t: i for i, t in enumerate(TRIPLES)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def covered(blocks):
    result = 0
    for block in blocks:
        for triple in it.combinations(block, 3):
            result |= 1 << TRANK[triple]
    return result


def transform(point, shift, phase):
    group, position = divmod(point - 1, 4)
    return 4 * ((group + shift) % 4) + ((position + phase) % 3 + 1 if position < 3 else 4)


def orbit_catalog():
    orbits = {}
    for block in it.combinations(range(1, 17), 5):
        if any(len(set(block) & anchor) > 1 for anchor in ANCHORS):
            continue
        orbit = tuple(
            sorted(
                {
                    tuple(sorted(transform(p, shift, phase) for p in block))
                    for shift in range(4)
                    for phase in range(3)
                }
            )
        )
        require(len(orbit) == 12, "short orbit")
        orbits[orbit[0]] = orbit
    require(
        len(orbits) == 100 and len({b for o in orbits.values() for b in o}) == 1200,
        "ordinary family is not partitioned",
    )
    return orbits


def main():
    orbits = orbit_catalog()
    masks = {rep: covered(orbit) for rep, orbit in orbits.items()}
    by_type = {
        n: sorted(rep for rep in orbits if sum(p % 4 != 0 for p in rep) == n) for n in [2, 3, 4]
    }
    cases = []
    for name, count, seed in [("matching", 12042, 2026100371), ("cycle", 25020, 2026100372)]:
        source = CATALOGS / name / "group-catalogs.json.gz"
        groups = json.loads(gzip.decompress(source.read_bytes()))
        expected_hash = {
            "matching": "84775683be806305fa6502e114b139c2b73eff31e9a2a3d798276176768744aa",
            "cycle": "fd41d8be92b70c1aecaca1bf3ea99d1beff32528a949ef91bfa9d4d5705a3d35",
        }
        require(sha(source) == expected_hash[name], "frozen108 catalog hash changed")
        pack = RAW / f"{name}-catalog.txt"
        rng = random.Random(seed)
        indices = [rng.randrange(count) for _ in range(4)]
        heavy = []
        with pack.open("w") as output:
            output.write(f"C64T1 {name} {count} {count} {count} {count}\n")
            for group, data in enumerate(groups):
                require(data["group"] == group and len(data["templates"]) == count, "catalog count")
                for index, template in enumerate(data["templates"]):
                    require(
                        len(template) == 7 and len(set(map(tuple, template))) == 7,
                        "template inventory",
                    )
                    degree = Counter(p for edge in template for p in edge)
                    require(
                        degree
                        == {
                            p: 2 if p == 4 * group + 4 else 1
                            for p in range(1, 17)
                            if p not in ANCHORS[group]
                        },
                        "template degree mismatch",
                    )
                    output.write(
                        " ".join(
                            map(
                                str, [group + 1, index + 1, *(p for edge in template for p in edge)]
                            )
                        )
                        + "\n"
                    )
                heavy.extend(
                    tuple(sorted(tuple(ANCHORS[group]) + tuple(edge)))
                    for edge in data["templates"][indices[group]]
                )
        heavy_mask = covered(heavy)
        choices = []
        for a in by_type[4]:
            for b, c in it.combinations(by_type[3], 2):
                choices.append(
                    (560 - (heavy_mask | masks[a] | masks[b] | masks[c]).bit_count(), (a, b, c))
                )
        for a, b in it.combinations(by_type[4], 2):
            for c in by_type[2]:
                choices.append(
                    (560 - (heavy_mask | masks[a] | masks[b] | masks[c]).bit_count(), (a, b, c))
                )
        holes, representatives = min(choices)
        ordinary = [block for rep in representatives for block in orbits[rep]]
        require(len(ordinary) == len(set(ordinary)) == 36, "ordinary duplicates")
        require(
            Counter(p for b in ordinary for p in b)
            == {p: 15 if p % 4 == 0 else 10 for p in range(1, 17)},
            "ordinary degrees",
        )
        blocks = sorted(heavy + ordinary)
        require(len(blocks) == len(set(blocks)) == 64, "seed duplicates")
        require(
            Counter(p for b in blocks for p in b) == {p: 20 for p in range(1, 17)}, "seed degrees"
        )
        require(560 - covered(blocks).bit_count() == holes, "seed objective mismatch")
        seed_path = HERE / f"{name}-seed.txt"
        seed_path.write_text("".join(" ".join(map(str, b)) + "\n" for b in blocks))
        cases.append(
            {
                "name": name,
                "seed": seed,
                "seconds": 300,
                "workers": 1,
                "catalog_path": str(pack.relative_to(ROOT)),
                "catalog_sha256": sha(pack),
                "source_catalog_path": str(source.relative_to(ROOT)),
                "source_catalog_sha256": sha(source),
                "templates_per_group": count,
                "seed_path": str(seed_path.relative_to(ROOT)),
                "seed_sha256": sha(seed_path),
                "template_ids_1based": [i + 1 for i in indices],
                "orbit_representatives": representatives,
                "initial_holes": holes,
                "seed_orbit_candidates": len(choices),
            }
        )
        print(
            json.dumps({k: cases[-1][k] for k in ["name", "initial_holes", "template_ids_1based"]})
        )
    (HERE / "seeds.json").write_text(
        json.dumps(
            {
                "cases": cases,
                "scope": "C4 x C3 rotation is initialization only; all search moves may break it.",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
